from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from flask_wtf.file import FileAllowed
from config import Config

class PropertyForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Descripción', validators=[DataRequired(), Length(min=20)])
    price = FloatField('Precio', validators=[DataRequired(), NumberRange(min=0)])
    currency = SelectField('Moneda', choices=[(c, c) for c in Config.CURRENCIES])
    property_type = SelectField('Tipo de Propiedad', choices=[(t, t) for t in Config.PROPERTY_TYPES])
    status = SelectField('Estado', choices=[(s, s) for s in Config.PROPERTY_STATUS])
    province = SelectField('Provincia', choices=[(p, p) for p in Config.PROVINCES])
    city = StringField('Ciudad', validators=[DataRequired(), Length(max=100)])
    address = StringField('Dirección', validators=[Length(max=200)])
    bedrooms = IntegerField('Habitaciones', validators=[Optional(), NumberRange(min=0)], default=0)
    bathrooms = IntegerField('Baños', validators=[Optional(), NumberRange(min=0)], default=0)
    area = FloatField('Área (m²)', validators=[Optional(), NumberRange(min=0)], default=0)
    lot_area = FloatField('Área del Terreno (m²)', validators=[Optional(), NumberRange(min=0)])
    year_built = IntegerField('Año de Construcción', validators=[Optional()])
    floors = IntegerField('Pisos', validators=[Optional(), NumberRange(min=1)], default=1)
    has_garage = BooleanField('Garaje')
    has_pool = BooleanField('Piscina')
    has_garden = BooleanField('Jardín')
    has_terrace = BooleanField('Terraza')
    has_ac = BooleanField('Aire Acondicionado')
    furnished = BooleanField('Amueblado')
    contact_name = StringField('Nombre de Contacto', validators=[Length(max=100)])
    contact_phone = StringField('Teléfono de Contacto', validators=[Length(max=20)])
    contact_email = StringField('Email de Contacto', validators=[Optional(), Email(), Length(max=120)])
    main_image = FileField('Imagen Principal', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'], 'Solo imágenes permitidas')])
    submit = SubmitField('Guardar Propiedad')
