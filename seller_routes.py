from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from decorators import seller_required
from models import db, Property, PropertyImage, Message
from forms import PropertyForm
from utils import save_image, delete_image
import os
from datetime import datetime

seller_bp = Blueprint('seller', __name__)

@seller_bp.route('/')
@login_required
@seller_required
def dashboard():
    total = Property.query.filter_by(user_id=current_user.id).count()
    available = Property.query.filter_by(user_id=current_user.id, status='Disponible').count()
    sold = Property.query.filter_by(user_id=current_user.id, status='Vendida').count()
    recent = Property.query.filter_by(user_id=current_user.id).order_by(Property.created_at.desc()).limit(5).all()
    # Mensajes no leídos para las propiedades del vendedor
    property_ids = [p.id for p in Property.query.filter_by(user_id=current_user.id).all()]
    unread_messages = Message.query.filter(Message.property_id.in_(property_ids), Message.is_read == False).count()
    return render_template('seller/dashboard.html', total=total, available=available, sold=sold, recent=recent, unread_messages=unread_messages)

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
            path = save_image(form.main_image.data)
            prop.main_image = path
        db.session.add(prop)
        db.session.commit()
        # Imágenes adicionales
        if form.additional_images.data:
            for img in form.additional_images.data:
                if img:
                    path = save_image(img)
                    pi = PropertyImage(property_id=prop.id, image_path=path, is_main=False)
                    db.session.add(pi)
            db.session.commit()
        flash('Propiedad creada exitosamente.', 'success')
        return redirect(url_for('seller.properties'))
    return render_template('seller/create_property.html', form=form)

@seller_bp.route('/property/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@seller_required
def edit_property(id):
    prop = Property.query.get_or_404(id)
    if prop.user_id != current_user.id and not current_user.is_admin():
        flash('No tienes permiso.', 'danger')
        return redirect(url_for('seller.properties'))
    form = PropertyForm(obj=prop)
    if form.validate_on_submit():
        form.populate_obj(prop)
        if form.main_image.data:
            if prop.main_image:
                delete_image(prop.main_image)
            path = save_image(form.main_image.data)
            prop.main_image = path
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
        flash('No tienes permiso.', 'danger')
        return redirect(url_for('seller.properties'))
    # Eliminar imágenes
    if prop.main_image:
        delete_image(prop.main_image)
    for img in prop.images:
        delete_image(img.image_path)
    db.session.delete(prop)
    db.session.commit()
    flash('Propiedad eliminada.', 'success')
    return redirect(url_for('seller.properties'))

@seller_bp.route('/messages')
@login_required
@seller_required
def messages():
    page = request.args.get('page', 1, type=int)
    property_ids = [p.id for p in Property.query.filter_by(user_id=current_user.id).all()]
    # Si no tiene propiedades, mostrar vacío
    if not property_ids:
        return render_template('seller/messages.html', messages=[], pagination=None)
    msgs = Message.query.filter(Message.property_id.in_(property_ids)).order_by(Message.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('seller/messages.html', messages=msgs)

@seller_bp.route('/message/<int:id>/read', methods=['POST'])
@login_required
@seller_required
def mark_read(id):
    msg = Message.query.get_or_404(id)
    # Verificar que el mensaje pertenece a una propiedad del vendedor
    if msg.property.user_id != current_user.id:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('seller.messages'))
    msg.is_read = True
    db.session.commit()
    flash('Mensaje marcado como leído.', 'success')
    return redirect(url_for('seller.messages'))
