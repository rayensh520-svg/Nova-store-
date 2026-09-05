from flask import jsonify, request, session

from . import seller_bp
from .models import Seller
from .service import SellerError, create_store
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


@seller_bp.post("/store")
@role_required("seller")
def create_seller_store():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "")
    description = data.get("description", "")

    seller = Seller.find_by_user_id(session["user_id"])

    if seller is None:
        return jsonify({
            "success": False,
            "error": "Seller profile not found."
        }), 404

    try:
        store_id = create_store(
            seller_id=seller.id,
            name=name,
            description=description,
        )

        return jsonify({
            "success": True,
            "store_id": store_id
        }), 201

    except SellerError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400
