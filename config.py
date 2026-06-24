import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///myhouseincuban.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ITEMS_PER_PAGE = 12
    CURRENCIES = ['USD', 'EUR', 'CUP', 'MLC']
    PROVINCES = [
        'Pinar del Río', 'Artemisa', 'La Habana', 'Mayabeque',
        'Matanzas', 'Cienfuegos', 'Villa Clara', 'Sancti Spíritus',
        'Ciego de Ávila', 'Camagüey', 'Las Tunas', 'Holguín',
        'Granma', 'Santiago de Cuba', 'Guantánamo', 'Isla de la Juventud'
    ]
    PROPERTY_TYPES = [
        'Casa', 'Apartamento', 'Penthouse', 'Casa Colonial',
        'Casa de Playa', 'Finca', 'Terreno', 'Local Comercial'
    ]
    PROPERTY_STATUS = ['Disponible', 'Vendida', 'Reservada', 'En negociación']
