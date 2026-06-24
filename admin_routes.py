from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from decorators import admin_required
from models import db, User, Property, Message, SiteSettings
from utils import get_property_stats
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = get_property_stats()
    recent_properties = Property.query.order_by(Property.created_at.desc()).limit(5).all()
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_properties = Property.query.filter(Property.created_at >= thirty_days_ago).count()
    new_users = User.query.filter(User.created_at >= thirty_days_ago, User.role == 'seller').count()
    new_messages = Message.query.filter(Message.created_at >= thirty_days_ago).count()
    return render_template('admin/dashboard.html', stats=stats, recent_properties=recent_properties, recent_messages=recent_messages, new_properties=new_properties, new_users=new_users, new_messages=new_messages)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    if user.is_admin():
        flash('No se puede desactivar un administrador.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'Usuario {"activado" if user.is_active else "desactivado"}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/properties')
@login_required
@admin_required
def properties():
    page = request.args.get('page', 1, type=int)
    properties = Property.query.order_by(Property.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/properties.html', properties=properties)

@admin_bp.route('/property/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_property(id):
    prop = Property.query.get_or_404(id)
    prop.is_active = not prop.is_active
    db.session.commit()
    flash(f'Propiedad {"activada" if prop.is_active else "desactivada"}', 'success')
    return redirect(url_for('admin.properties'))

@admin_bp.route('/property/<int:id>/feature', methods=['POST'])
@login_required
@admin_required
def toggle_feature(id):
    prop = Property.query.get_or_404(id)
    prop.is_featured = not prop.is_featured
    db.session.commit()
    flash(f'Propiedad {"destacada" if prop.is_featured else "no destacada"}', 'success')
    return redirect(url_for('admin.properties'))

@admin_bp.route('/messages')
@login_required
@admin_required
def messages():
    page = request.args.get('page', 1, type=int)
    messages = Message.query.order_by(Message.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/messages.html', messages=messages)

@admin_bp.route('/stats')
@login_required
@admin_required
def stats():
    from sqlalchemy import func
    by_province = db.session.query(Property.province, func.count(Property.id)).group_by(Property.province).all()
    by_type = db.session.query(Property.property_type, func.count(Property.id)).group_by(Property.property_type).all()
    most_viewed = Property.query.order_by(Property.views.desc()).limit(10).all()
    return render_template('admin/stats.html', by_province=by_province, by_type=by_type, most_viewed=most_viewed)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    if request.method == 'POST':
        settings.site_name = request.form.get('site_name')
        settings.site_description = request.form.get('site_description')
        settings.contact_email = request.form.get('contact_email')
        settings.contact_phone = request.form.get('contact_phone')
        db.session.commit()
        flash('Configuración actualizada', 'success')
        return redirect(url_for('admin.settings'))
    return render_template('admin/settings.html', settings=settings)
