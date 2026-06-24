from flask import Blueprint, render_template, request, jsonify, current_app
from models import Property, db
from sqlalchemy import or_
from config import Config
import logging

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured = Property.query.filter_by(is_featured=True, is_active=True, status='Disponible').order_by(Property.created_at.desc()).limit(8).all()
    latest = Property.query.filter_by(is_active=True, status='Disponible').order_by(Property.created_at.desc()).limit(6).all()
    return render_template('index.html', featured=featured, latest=latest, provinces=Config.PROVINCES, property_types=Config.PROPERTY_TYPES)

@main_bp.route('/search')
def search():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    ptype = request.args.get('type', '')
    province = request.args.get('province', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    currency = request.args.get('currency', '')
    bedrooms = request.args.get('bedrooms', type=int)
    bathrooms = request.args.get('bathrooms', type=int)
    sort = request.args.get('sort', 'newest')
    
    query = Property.query.filter_by(is_active=True, status='Disponible')
    
    if q:
        query = query.filter(or_(Property.title.ilike(f'%{q}%'), Property.description.ilike(f'%{q}%'), Property.city.ilike(f'%{q}%')))
    if ptype:
        query = query.filter_by(property_type=ptype)
    if province:
        query = query.filter_by(province=province)
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if currency:
        query = query.filter_by(currency=currency)
    if bedrooms:
        query = query.filter(Property.bedrooms >= bedrooms)
    if bathrooms:
        query = query.filter(Property.bathrooms >= bathrooms)
    
    if sort == 'price_asc':
        query = query.order_by(Property.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Property.price.desc())
    else:
        query = query.order_by(Property.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
    return render_template('search.html', properties=pagination.items, pagination=pagination, provinces=Config.PROVINCES, property_types=Config.PROPERTY_TYPES, currencies=Config.CURRENCIES)

@main_bp.route('/property/<int:id>')
def property_detail(id):
    property = Property.query.get_or_404(id)
    property.views += 1
    db.session.commit()
    related = Property.query.filter(Property.id != id, Property.province == property.province, Property.is_active == True, Property.status == 'Disponible').limit(4).all()
    # Obtener todas las imágenes
    images = [property.main_image] + [img.image_path for img in property.images if img.image_path]
    images = [img for img in images if img]  # eliminar None
    return render_template('property_detail.html', property=property, related=related, images=images)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        from models import Message
        msg = Message(
            property_id=request.form.get('property_id', 0),
            sender_name=request.form.get('name'),
            sender_email=request.form.get('email'),
            sender_phone=request.form.get('phone'),
            message=request.form.get('message')
        )
        db.session.add(msg)
        db.session.commit()
        # Log
        current_app.logger.info(f'Nuevo mensaje de {msg.sender_name} para propiedad {msg.property_id}')
        from flask import flash
        flash('Mensaje enviado con éxito. El vendedor se pondrá en contacto.', 'success')
        return redirect(request.referrer or url_for('main.index'))
    return render_template('contact.html')
