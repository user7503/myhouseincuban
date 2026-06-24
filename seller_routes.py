from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from decorators import seller_required
from models import db, Property, PropertyImage, Message
from forms import PropertyForm
from utils import save_image
import os

seller_bp = Blueprint('seller', __name__)

@seller_bp.route('/')
@login_required
@seller_required
def dashboard():
    total_properties = Property.query.filter_by(user_id=current_user.id).count()
    available_properties = Property.query.filter_by(user_id=current_user.id, status='Disponible').count()
    sold_properties = Property.query.filter_by(user_id=current_user.id, status='Vendida').count()
    recent_properties = Property.query.filter_by(user_id=current_user.id).order_by(Property.created_at.desc()).limit(5).all()
    return render_template('seller/dashboard.html', total_properties=total_properties, available_properties=available_properties, sold_properties=sold_properties, recent_properties=recent_properties)

@seller_bp.route('/properties')
@login_required
@seller_required
def properties():
    page = request.args.get('page', 1, type=int)
    properties = Property.query.filter_by(user_id=current_user.id).order_by(Property.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('seller/properties.html', properties=properties)

@seller_bp.route('/property/create', methods=['GET', 'POST'])
@login_required
@seller_required
def create_property():
    form = PropertyForm()
    if form.validate_on_submit():
        property = Property(
            title=form.title.data, description=form.description.data,
            price=form.price.data, currency=form.currency.data,
            property_type=form.property_type.data, status=form.status.data,
            province=form.province.data, city=form.city.data,
            address=form.address.data, bedrooms=form.bedrooms.data,
            bathrooms=form.bathrooms.data, area=form.area.data,
            lot_area=form.lot_area.data, year_built=form.year_built.data,
            floors=form.floors.data, has_garage=form.has_garage.data,
            has_pool=form.has_pool.data, has_garden=form.has_garden.data,
            has_terrace=form.has_terrace.data, has_ac=form.has_ac.data,
            furnished=form.furnished.data, contact_name=form.contact_name.data or current_user.username,
            contact_phone=form.contact_phone.data or current_user.phone,
            contact_email=form.contact_email.data or current_user.email,
            user_id=current_user.id
        )
        if form.main_image.data:
            image_path = save_image(form.main_image.data)
            property.main_image = image_path
        db.session.add(property)
        db.session.commit()
        
        # Guardar imágenes adicionales
        if form.additional_images.data:
            for img in form.additional_images.data:
                img_path = save_image(img)
                extra = PropertyImage(property_id=property.id, image_path=img_path, is_main=False)
                db.session.add(extra)
            db.session.commit()
        
        flash('Propiedad creada exitosamente!', 'success')
        return redirect(url_for('seller.properties'))
    return render_template('seller/create_property.html', form=form)

@seller_bp.route('/property/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@seller_required
def edit_property(id):
    property = Property.query.get_or_404(id)
    if property.user_id != current_user.id and not current_user.is_admin():
        flash('No tienes permiso para editar esta propiedad.', 'danger')
        return redirect(url_for('seller.properties'))
    form = PropertyForm(obj=property)
    if form.validate_on_submit():
        form.populate_obj(property)
        if form.main_image.data:
            if property.main_image:
                old_image_path = os.path.join(current_app.root_path, 'static', property.main_image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            image_path = save_image(form.main_image.data)
            property.main_image = image_path
        db.session.commit()
        flash('Propiedad actualizada exitosamente!', 'success')
        return redirect(url_for('seller.properties'))
    return render_template('seller/edit_property.html', form=form, property=property)

@seller_bp.route('/property/<int:id>/delete', methods=['POST'])
@login_required
@seller_required
def delete_property(id):
    property = Property.query.get_or_404(id)
    if property.user_id != current_user.id and not current_user.is_admin():
        flash('No tienes permiso para eliminar esta propiedad.', 'danger')
        return redirect(url_for('seller.properties'))
    if property.main_image:
        image_path = os.path.join(current_app.root_path, 'static', property.main_image)
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(property)
    db.session.commit()
    flash('Propiedad eliminada exitosamente!', 'success')
    return redirect(url_for('seller.properties'))

@seller_bp.route('/messages')
@login_required
@seller_required
def messages():
    page = request.args.get('page', 1, type=int)
    property_ids = [p.id for p in Property.query.filter_by(user_id=current_user.id).all()]
    messages = Message.query.filter(Message.property_id.in_(property_ids)).order_by(Message.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('seller/messages.html', messages=messages)
