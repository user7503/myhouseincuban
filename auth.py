from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('seller.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Tu cuenta ha sido desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user, remember=remember)
            flash(f'Bienvenido {user.username}!', 'success')
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('seller.dashboard'))
        flash('Email o contraseña incorrectos.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        
        if User.query.filter_by(email=email).first():
            flash('Este email ya está registrado.', 'danger')
            return redirect(url_for('auth.register'))
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(username=username, email=email, password=generate_password_hash(password), phone=phone, role='seller')
        db.session.add(user)
        db.session.commit()
        flash('Registro exitoso! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username')
        current_user.phone = request.form.get('phone')
        if request.form.get('password'):
            if request.form.get('password') == request.form.get('confirm_password'):
                current_user.password = generate_password_hash(request.form.get('password'))
            else:
                flash('Las contraseñas no coinciden.', 'danger')
                return redirect(url_for('auth.profile'))
        db.session.commit()
        flash('Perfil actualizado exitosamente!', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html')
