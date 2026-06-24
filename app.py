import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, User
from routes import main_bp
from auth import auth_bp
from admin_routes import admin_bp
from seller_routes import seller_bp
from werkzeug.security import generate_password_hash
import logging
from logging.handlers import RotatingFileHandler

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Seguridad CSRF
    csrf = CSRFProtect(app)
    
    # Base de datos
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(seller_bp, url_prefix='/seller')
    
    # Crear tablas y usuario por defecto
    with app.app_context():
        db.create_all()
        create_default_users()
    
    # Configurar logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/myhouse.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('MyHouseinCuban startup')
    
    return app

def create_default_users():
    if not User.query.filter_by(email='admin@myhouseincuban.com').first():
        admin = User(
            username='Admin',
            email='admin@myhouseincuban.com',
            password=generate_password_hash('admin123'),
            role='admin',
            phone='+5355123456',
            is_active=True
        )
        db.session.add(admin)
    
    if not User.query.filter_by(email='seller@myhouseincuban.com').first():
        seller = User(
            username='Vendedor Demo',
            email='seller@myhouseincuban.com',
            password=generate_password_hash('seller123'),
            role='seller',
            phone='+5355654321',
            is_active=True
        )
        db.session.add(seller)
    
    db.session.commit()

app = create_app()
