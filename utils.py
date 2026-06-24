import os
import secrets
from PIL import Image
from flask import current_app

def save_image(form_image, folder='uploads', size=(800, 600)):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    image_fn = random_hex + f_ext
    image_path = os.path.join(current_app.root_path, 'static', folder, image_fn)
    i = Image.open(form_image)
    i.thumbnail(size)
    i.save(image_path)
    return os.path.join(folder, image_fn)

def get_property_stats():
    from models import Property, User, Message
    stats = {
        'total_properties': Property.query.count(),
        'available_properties': Property.query.filter_by(status='Disponible').count(),
        'sold_properties': Property.query.filter_by(status='Vendida').count(),
        'total_users': User.query.filter_by(role='seller').count(),
        'total_messages': Message.query.count(),
        'unread_messages': Message.query.filter_by(is_read=False).count()
    }
    return stats
