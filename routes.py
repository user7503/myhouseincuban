from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Property, PropertyView, Conversation, Message, User
from sqlalchemy import or_
from config import Config
import requests
import logging

main_bp = Blueprint('main', __name__)

def get_geolocation_province(ip):
    try:
        if ip in ('127.0.0.1', 'localhost'):
            ip = '190.6.45.0'   # IP de prueba (La Habana)
        resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
        if resp.status_code == 200:
            return resp.json().get('regionName', 'La Habana')
    except:
        pass
    return 'La Habana'

@main_bp.route('/')
def index():
    visitor_ip = request.remote_addr
    province = request.args.get('province') or get_geolocation_province(visitor_ip)
    suggested = Property.query.filter_by(province=province, is_active=True, status='Disponible').order_by(Property.views.desc()).limit(8).all()
    featured = Property.query.filter_by(is_featured=True, is_active=True, status='Disponible').order_by(Property.created_at.desc()).limit(8).all()
    latest = Property.query.filter_by(is_active=True, status='Disponible').order_by(Property.created_at.desc()).limit(6).all()
    return render_template('index.html', suggested=suggested, featured=featured, latest=latest,
                           province=province, provinces=Config.PROVINCES, property_types=Config.PROPERTY_TYPES)

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
    return render_template('search.html', properties=pagination.items, pagination=pagination,
                           provinces=Config.PROVINCES, property_types=Config.PROPERTY_TYPES, currencies=Config.CURRENCIES)

@main_bp.route('/property/<int:id>')
def property_detail(id):
    prop = Property.query.get_or_404(id)
    prop.views += 1
    db.session.commit()

    if current_user.is_authenticated:
        view = PropertyView(user_id=current_user.id, property_id=prop.id)
        db.session.add(view)
        db.session.commit()

    related = Property.query.filter(Property.id != id, Property.province == prop.province,
                                    Property.is_active == True, Property.status == 'Disponible').limit(4).all()
    images = [img.image_path for img in prop.images if img.image_path]
    if prop.main_image:
        images.insert(0, prop.main_image)
    images = [img for img in images if img]

    conversation = None
    if current_user.is_authenticated and current_user.id != prop.user_id:
        conversation = Conversation.query.filter_by(property_id=prop.id, buyer_id=current_user.id, seller_id=prop.user_id).first()

    return render_template('property_detail.html', property=prop, related=related, images=images, conversation=conversation)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

# --- Mensajería ---
@main_bp.route('/conversation/start/<int:property_id>', methods=['POST'])
@login_required
def start_conversation(property_id):
    prop = Property.query.get_or_404(property_id)
    if current_user.id == prop.user_id:
        flash('No puedes enviarte mensajes a ti mismo.', 'danger')
        return redirect(url_for('main.property_detail', id=property_id))

    conv = Conversation.query.filter_by(property_id=prop.id, buyer_id=current_user.id, seller_id=prop.user_id).first()
    if not conv:
        conv = Conversation(property_id=prop.id, buyer_id=current_user.id, seller_id=prop.user_id)
        db.session.add(conv)
        db.session.commit()

    text = request.form.get('message', '').strip()
    if not text:
        flash('El mensaje no puede estar vacío.', 'danger')
        return redirect(url_for('main.property_detail', id=property_id))

    msg = Message(conversation_id=conv.id, sender_id=current_user.id, message=text)
    db.session.add(msg)
    db.session.commit()
    flash('Mensaje enviado.', 'success')
    return redirect(url_for('main.view_conversation', conv_id=conv.id))

@main_bp.route('/messages')
@login_required
def messages_inbox():
    convs = Conversation.query.filter(
        (Conversation.buyer_id == current_user.id) | (Conversation.seller_id == current_user.id)
    ).order_by(Conversation.created_at.desc()).all()
    return render_template('messages/inbox.html', conversations=convs)

@main_bp.route('/messages/<int:conv_id>')
@login_required
def view_conversation(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    if current_user.id not in (conv.buyer_id, conv.seller_id):
        abort(403)
    for msg in conv.messages:
        if msg.sender_id != current_user.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()
    return render_template('messages/conversation.html', conversation=conv)

@main_bp.route('/messages/<int:conv_id>/send', methods=['POST'])
@login_required
def send_message_in_conversation(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    if current_user.id not in (conv.buyer_id, conv.seller_id):
        abort(403)
    text = request.form.get('message', '').strip()
    if not text:
        flash('Mensaje vacío.', 'danger')
        return redirect(url_for('main.view_conversation', conv_id=conv_id))
    msg = Message(conversation_id=conv.id, sender_id=current_user.id, message=text)
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for('main.view_conversation', conv_id=conv_id))
