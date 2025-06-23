from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

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

    ######## Endpoints for video ########

    from app.routes.video_rtsp import video_bp

    app.register_blueprint(video_bp)


    ######## Endpoints for clips ########

    from app.routes.manage_clips import clips_bp

    app.register_blueprint(clips_bp)

    
    return app