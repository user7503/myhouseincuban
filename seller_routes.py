from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from decorators import seller_required
from models import db, Property, PropertyImage, Message, Conversation, Plan
from forms import PropertyForm
from utils import save_image, delete_image
from datetime import datetime, timedelta

seller_bp = Blueprint('seller', __name__)

@seller_bp.route('/')
@login_required
@seller_required
def dashboard():
    total = Property.query.filter_by(user_id=current_user.id).count()
    available = Property.query.filter_by(user_id=current_user.id, status='Disponible').count()
    sold = Property.query.filter_by(user_id=current_user.id, status='Vendida').count()
    recent = Property.query.filter_by(user_id=current_user.id).order_by(Property.created_at.desc()).limit(5).all()
    unread = Message.query.join(Conversation).filter(
        Conversation.seller_id == current_user.id,
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).count()
    return render_template('seller/dashboard.html', total=total, available=available, sold=sold, recent=recent, unread_messages=unread)

@seller_bp.route('/properties')
@login_required
@seller_required
def properties():
    page = request.args.get('page', 1, type=int)
    props = Property.query.filter_by(user_id=current_user.id).order_by(Property.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('seller/properties.html', properties=props)

@seller_bp.route('/property/create', methods=['GET', 'POST'])
@login_required
@seller_required
def create_property():
    if not current_user.can_publish_more():
        flash('Límite de propiedades alcanzado. Actualiza tu plan.', 'warning')
        return redirect(url_for('seller.plans'))
    form = PropertyForm()
    if form.validate_on_submit():
        prop = Property(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            currency=form.currency.data,
            property_type=form.property_type.data,
            status=form.status.data,
            province=form.province.data,
            city=form.city.data,
            address=form.address.data,
            bedrooms=form.bedrooms.data or 0,
            bathrooms=form.bathrooms.data or 0,
            area=form.area.data or 0,
            lot_area=form.lot_area.data,
            year_built=form.year_built.data,
            floors=form.floors.data or 1,
            has_garage=form.has_garage.data,
            has_pool=form.has_pool.data,
            has_garden=form.has_garden.data,
            has_terrace=form.has_terrace.data,
            has_ac=form.has_ac.data,
            furnished=form.furnished.data,
            contact_name=form.contact_name.data or current_user.username,
            contact_phone=form.contact_phone.data or current_user.phone,
            contact_email=form.contact_email.data or current_user.email,
            user_id=current_user.id
        )
        if form.main_image.data:
            prop.main_image = save_image(form.main_image.data)
        db.session.add(prop)
        db.session.flush()
        if form.additional_images.data:
            for img in form.additional_images.data:
                if img:
                    pi = PropertyImage(property_id=prop.id, image_path=save_image(img))
                    db.session.add(pi)
        current_user.properties_count += 1
        db.session.commit()
        flash('Propiedad creada.', 'success')
        return redirect(url_for('seller.properties'))
    return render_template('seller/create_property.html', form=form)

@seller_bp.route('/property/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@seller_required
def edit_property(id):
    prop = Property.query.get_or_404(id)
    if prop.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    form = PropertyForm(obj=prop)
    if form.validate_on_submit():
        form.populate_obj(prop)
        if form.main_image.data:
            if prop.main_image:
                delete_image(prop.main_image)
            prop.main_image = save_image(form.main_image.data)
        db.session.commit()
        flash('Propiedad actualizada.', 'success')
        return redirect(url_for('seller.properties'))
    return render_template('seller/edit_property.html', form=form, property=prop)

@seller_bp.route('/property/<int:id>/delete', methods=['POST'])
@login_required
@seller_required
def delete_property(id):
    prop = Property.query.get_or_404(id)
    if prop.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    if prop.main_image:
        delete_image(prop.main_image)
    for img in prop.images:
        delete_image(img.image_path)
    current_user.properties_count = max(0, current_user.properties_count - 1)
    db.session.delete(prop)
    db.session.commit()
    flash('Propiedad eliminada.', 'success')
    return redirect(url_for('seller.properties'))

@seller_bp.route('/property/<int:id>/feature', methods=['POST'])
@login_required
@seller_required
def feature_property(id):
    prop = Property.query.get_or_404(id)
    if prop.user_id != current_user.id:
        abort(403)
    if not current_user.plan.can_feature:
        flash('Tu plan no permite destacar.', 'warning')
        return redirect(url_for('seller.plans'))
    if prop.is_featured:
        prop.is_featured = False
        prop.featured_until = None
        flash('Ya no está destacada.', 'info')
    else:
        prop.is_featured = True
        prop.featured_until = datetime.utcnow() + timedelta(days=30)
        flash('Propiedad destacada 30 días.', 'success')
    db.session.commit()
    return redirect(url_for('seller.properties'))

@seller_bp.route('/plans')
@login_required
@seller_required
def plans():
    plans = Plan.query.all()
    return render_template('plans/plans.html', plans=plans)

@seller_bp.route('/plans/upgrade/<int:plan_id>', methods=['POST'])
@login_required
@seller_required
def upgrade_plan(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    # Simula pago
    current_user.plan_id = plan.id
    current_user.subscription_expires = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    flash(f'Plan actualizado a {plan.name}.', 'success')
    return redirect(url_for('seller.plans'))
