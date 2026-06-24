from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from decorators import admin_required
from models import db, User, Property, Message, SiteSettings, Plan, Conversation
from utils import get_property_stats
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = get_property_stats()
    recent_props = Property.query.order_by(Property.created_at.desc()).limit(5).all()
    recent_convs = Conversation.query.order_by(Conversation.created_at.desc()).limit(5).all()
    thirty_days = datetime.utcnow() - timedelta(days=30)
    new_props = Property.query.filter(Property.created_at >= thirty_days).count()
    new_users = User.query.filter(User.created_at >= thirty_days, User.role == 'seller').count()
    new_msgs = Message.query.filter(Message.created_at >= thirty_days).count()
    return render_template('admin/dashboard.html', stats=stats, recent_properties=recent_props,
                           recent_convs=recent_convs, new_properties=new_props, new_users=new_users, new_messages=new_msgs)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users, Plan=Plan)

@admin_bp.route('/user/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    if user.is_admin():
        flash('No se puede desactivar un admin.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'Usuario {"activado" if user.is_active else "desactivado"}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/user/<int:id>/plan', methods=['POST'])
@login_required
@admin_required
def change_user_plan(id):
    user = User.query.get_or_404(id)
    plan_id = request.form.get('plan_id', type=int)
    plan = Plan.query.get(plan_id)
    if plan:
        user.plan_id = plan.id
        db.session.commit()
        flash(f'Plan de {user.username} cambiado a {plan.name}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/properties')
@login_required
@admin_required
def properties():
    page = request.args.get('page', 1, type=int)
    props = Property.query.order_by(Property.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/properties.html', properties=props)

@admin_bp.route('/property/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_property(id):
    prop = Property.query.get_or_404(id)
    prop.is_active = not prop.is_active
    db.session.commit()
    flash(f'Propiedad {"activada" if prop.is_active else "desactivada"}.', 'success')
    return redirect(url_for('admin.properties'))

@admin_bp.route('/property/<int:id>/feature', methods=['POST'])
@login_required
@admin_required
def toggle_feature(id):
    prop = Property.query.get_or_404(id)
    if prop.is_featured:
        prop.is_featured = False
        prop.featured_until = None
    else:
        prop.is_featured = True
        prop.featured_until = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    flash('Destacado actualizado.', 'success')
    return redirect(url_for('admin.properties'))

@admin_bp.route('/conversations')
@login_required
@admin_required
def conversations():
    page = request.args.get('page', 1, type=int)
    convs = Conversation.query.order_by(Conversation.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/conversations.html', conversations=convs)

@admin_bp.route('/plans')
@login_required
@admin_required
def plans():
    plans = Plan.query.all()
    return render_template('admin/plans.html', plans=plans)

@admin_bp.route('/plans/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_plan(id):
    plan = Plan.query.get_or_404(id)
    if request.method == 'POST':
        plan.name = request.form.get('name')
        plan.max_properties = int(request.form.get('max_properties', 0))
        plan.can_feature = 'can_feature' in request.form
        plan.price_monthly = float(request.form.get('price_monthly', 0))
        db.session.commit()
        flash('Plan actualizado.', 'success')
        return redirect(url_for('admin.plans'))
    return render_template('admin/edit_plan.html', plan=plan)

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
        flash('Configuración actualizada.', 'success')
        return redirect(url_for('admin.settings'))
    return render_template('admin/settings.html', settings=settings)
