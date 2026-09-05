from flask import jsonify, session

from . import seller_bp
from .models import Seller
from .store import Store
from app.auth.guards import role_required


@seller_bp.get("/me")
@role_required("seller")
def seller_profile():
    seller = Seller.find_by_user_id(session["user_id"])

    if seller is None:
        return jsonify({
            "success": False,
            "error": "Seller profile not found."
        }), 404

    return jsonify({
        "success": True,
        "seller": {
            "id": seller.id,
            "user_id": seller.user_id,
            "verification_status": seller.verification_status,
            "is_active": seller.is_active
        }
    })


@seller_bp.get("/store")
@role_required("seller")
def seller_store():
    seller = Seller.find_by_user_id(session["user_id"])

    if seller is None:
        return jsonify({
            "success": False,
            "error": "Seller profile not found."
        }), 404

    store = Store.find_by_seller_id(seller.id)

    if store is None:
        return jsonify({
            "success": True,
            "store": None
        })

    return jsonify({
        "success": True,
        "store": {
            "id": store.id,
            "seller_id": store.seller_id,
            "name": store.name,
            "description": store.description,
            "is_visible": store.is_visible
        }
    })
