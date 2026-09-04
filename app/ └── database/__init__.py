from flask import Flask

from config import Config
from app.auth import auth_bp
from app.auth import routes
from app.database import get_connection
from app.database.init_db import initialize_database


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    initialize_database()

    app.register_blueprint(auth_bp)

    return app
