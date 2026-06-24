# MyHouseinCuban

Plataforma profesional de venta de propiedades en Cuba.

## Características
- Recomendaciones geolocalizadas
- Mensajería en tiempo real
- Planes de suscripción (Free/Premium/Business)
- Panel de administración completo
- Búsqueda avanzada con filtros colapsables
- Tres roles: Admin, Vendedor, Usuario (comprador)
- Diseño responsive

## Despliegue en Render
1. Sube este proyecto a GitHub.
2. Crea un Web Service con Start Command: `gunicorn -b 0.0.0.0:$PORT app:app`
3. Agrega variable de entorno `SECRET_KEY` con un valor seguro.
4. La base de datos SQLite se creará automáticamente (para producción usa PostgreSQL).
