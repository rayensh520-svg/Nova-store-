from flask import Blueprint


seller_bp = Blueprint(
    "seller",
    __name__,
    url_prefix="/api/v1/seller"
)


from . import routes
