from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
import logging
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Probar conexión a la base de datos y mostrar mensaje si es exitosa
    with app.app_context():
        try:
            db.session.execute(text('SELECT 1'))
            app.logger.info('✅ Conexión exitosa con la base de datos PostgreSQL.')
        except OperationalError as e:
            app.logger.error(f'❌ Error al conectar con la base de datos: {e}')

    ######## Endpoints for login ########

    from app.login.controllers.login_controller import users_bp

    app.register_blueprint(users_bp)


    ######## Endpoints for cameras ########

    from app.cameras.controllers.cameras_controller import cameras_bp
    from app.cameras.controllers.alerts_controller import alerts_bp
    from app.cameras.controllers.zones_controller import zones_bp

    app.register_blueprint(cameras_bp)
    app.register_blueprint(zones_bp)
    app.register_blueprint(alerts_bp)

 

    
    return app