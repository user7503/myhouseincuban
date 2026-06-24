from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db, Plan
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Cuenta desactivada.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user, remember=remember)
            flash(f'¡Bienvenido {user.username}!', 'success')
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('seller.dashboard'))
        flash('Email o contraseña incorrectos.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    plans = Plan.query.all()
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        phone = request.form.get('phone')
        plan_id = request.form.get('plan_id', 1, type=int)

        if User.query.filter_by(email=email).first():
            flash('Email ya registrado.', 'danger')
            return redirect(url_for('auth.register'))
        if password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('auth.register'))
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return redirect(url_for('auth.register'))

        user = User(username=username, email=email, password=generate_password_hash(password),
                    phone=phone, role='seller', plan_id=plan_id)
        db.session.add(user)
        db.session.commit()
        flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', plans=plans)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username')
        current_user.phone = request.form.get('phone')
        new_pass = request.form.get('password')
        if new_pass:
            if new_pass == request.form.get('confirm_password'):
                current_user.password = generate_password_hash(new_pass)
            else:
                flash('Las contraseñas no coinciden.', 'danger')
                return redirect(url_for('auth.profile'))
        db.session.commit()
        flash('Perfil actualizado.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html')
