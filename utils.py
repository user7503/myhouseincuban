import os
import secrets
from PIL import Image
from flask import current_app

def save_image(form_image, folder='uploads', size=(800, 600)):
    upload_folder = os.path.join(current_app.root_path, 'static', folder)
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    image_fn = random_hex + f_ext
    image_path = os.path.join(upload_folder, image_fn)
    i = Image.open(form_image)
    i.thumbnail(size)
    i.save(image_path, optimize=True, quality=85)
    return os.path.join(folder, image_fn)

def delete_image(image_path):
    if image_path:
        full_path = os.path.join(current_app.root_path, 'static', image_path)
        if os.path.exists(full_path):
            os.remove(full_path)

def get_property_stats():
    from models import Property, User, Message
    return {
        'total_properties': Property.query.count(),
        'available_properties': Property.query.filter_by(status='Disponible').count(),
        'sold_properties': Property.query.filter_by(status='Vendida').count(),
        'total_users': User.query.filter(User.role != 'admin').count(),
        'total_messages': Message.query.count(),
        'unread_messages': Message.query.filter_by(is_read=False).count()
    }
