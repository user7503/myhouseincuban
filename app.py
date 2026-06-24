import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from models import db, User
from routes import main_bp
from auth import auth_bp
from admin_routes import admin_bp
from seller_routes import seller_bp
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
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
        create_default_users()
    
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

#if __name__ == '__main__':
app = create_app()
#    app.run(debug=True, host='0.0.0.0', port=5000)
