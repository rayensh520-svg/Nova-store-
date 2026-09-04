from flask import Flask

from config import Config
from app.auth import auth_bp
from app.auth import routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)

    return app
