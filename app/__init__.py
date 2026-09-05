from flask import Flask

from config import Config
from app.auth import auth_bp
from app.database.init_db import initialize_database
from app.sellers import seller_bp
from app.sellers import routes


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    initialize_database()

    app.register_blueprint(auth_bp)
    app.register_blueprint(seller_bp)

    return app
