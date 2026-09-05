from flask import Flask

from config import Config

from app.auth import auth_bp
from app.auth import routes as auth_routes

from app.database.init_db import initialize_database

from app.sellers import seller_bp
from app.sellers import routes as seller_routes

from app.catalog import catalog_bp
from app.catalog import routes as catalog_routes


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    initialize_database()

    # Authentication
    app.register_blueprint(auth_bp)

    # Sellers & Stores
    app.register_blueprint(seller_bp)

    # Catalog & Products
    app.register_blueprint(catalog_bp)

    return app
