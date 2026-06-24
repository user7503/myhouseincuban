from flask import Blueprint, render_template, request, jsonify
from models import Property, db
from sqlalchemy import or_
from config import Config

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_properties = Property.query.filter_by(is_featured=True, is_active=True, status='Disponible').order_by(Property.created_at.desc()).limit(8).all()
    latest_properties = Property.query.filter_by(is_active=True, status='Disponible').order_by(Property.created_at.desc()).limit(6).all()
    return render_template('index.html', featured_properties=featured_properties, latest_properties=latest_properties, provinces=Config.PROVINCES, property_types_list=Config.PROPERTY_TYPES)

@main_bp.route('/search')
def search():
    page = request.args.get('page', 1, type=int)
    query = request.args.get('q', '')
    property_type = request.args.get('type', '')
    province = request.args.get('province', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    currency = request.args.get('currency', '')
    bedrooms = request.args.get('bedrooms', type=int)
    
    properties_query = Property.query.filter_by(is_active=True, status='Disponible')
    
    if query:
        properties_query = properties_query.filter(or_(Property.title.ilike(f'%{query}%'), Property.description.ilike(f'%{query}%'), Property.city.ilike(f'%{query}%')))
    if property_type:
        properties_query = properties_query.filter_by(property_type=property_type)
    if province:
        properties_query = properties_query.filter_by(province=province)
    if min_price:
        properties_query = properties_query.filter(Property.price >= min_price)
    if max_price:
        properties_query = properties_query.filter(Property.price <= max_price)
    if currency:
        properties_query = properties_query.filter_by(currency=currency)
    if bedrooms:
        properties_query = properties_query.filter(Property.bedrooms >= bedrooms)
    
    sort_by = request.args.get('sort', 'newest')
    if sort_by == 'price_asc':
        properties_query = properties_query.order_by(Property.price.asc())
    elif sort_by == 'price_desc':
        properties_query = properties_query.order_by(Property.price.desc())
    else:
        properties_query = properties_query.order_by(Property.created_at.desc())
    
    pagination = properties_query.paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
    properties = pagination.items
    
    return render_template('search.html', properties=properties, pagination=pagination, provinces=Config.PROVINCES, property_types=Config.PROPERTY_TYPES, currencies=Config.CURRENCIES)

@main_bp.route('/property/<int:id>')
def property_detail(id):
    property = Property.query.get_or_404(id)
    property.views += 1
    db.session.commit()
    related_properties = Property.query.filter(Property.id != id, Property.province == property.province, Property.is_active == True, Property.status == 'Disponible').limit(4).all()
    return render_template('property_detail.html', property=property, related_properties=related_properties)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        from models import Message
        message = Message(property_id=request.form.get('property_id', 0), sender_name=request.form.get('name'), sender_email=request.form.get('email'), sender_phone=request.form.get('phone'), message=request.form.get('message'))
        db.session.add(message)
        db.session.commit()
        from flask import flash
        flash('Mensaje enviado exitosamente!', 'success')
    return render_template('contact.html')
