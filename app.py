import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, User, Plan, Conversation, Message
from routes import main_bp
from auth import auth_bp
from admin_routes import admin_bp
from seller_routes import seller_bp
from werkzeug.security import generate_password_hash
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf.init_app(app)

    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(seller_bp, url_prefix='/seller')

    with app.app_context():
        db.create_all()
        create_default_data()

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/myhouse.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('MyHouseinCuban startup')

    return app

def create_default_data():
    # Planes
    if not Plan.query.first():
        free = Plan(name='Gratuito', max_properties=2, can_feature=False, price_monthly=0)
        premium = Plan(name='Premium', max_properties=10, can_feature=True, price_monthly=9.99)
        business = Plan(name='Business', max_properties=0, can_feature=True, price_monthly=29.99)
        db.session.add_all([free, premium, business])
        db.session.commit()

    # Admin
    if not User.query.filter_by(email='admin@myhouseincuban.com').first():
        admin = User(
            username='Admin',
            email='admin@myhouseincuban.com',
            password=generate_password_hash('admin123'),
            role='admin',
            phone='+5355123456',
            is_active=True,
            plan_id=Plan.query.filter_by(name='Business').first().id
        )
        db.session.add(admin)

    # Seller demo
    if not User.query.filter_by(email='seller@myhouseincuban.com').first():
        seller = User(
            username='Vendedor Demo',
            email='seller@myhouseincuban.com',
            password=generate_password_hash('seller123'),
            role='seller',
            phone='+5355654321',
            is_active=True,
            plan_id=Plan.query.filter_by(name='Gratuito').first().id
        )
        db.session.add(seller)

    db.session.commit()

app = create_app()

