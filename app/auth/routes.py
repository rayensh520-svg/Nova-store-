from flask import jsonify, request

from . import auth_bp
from .service import RegistrationError, register_user


@auth_bp.get("/status")
def auth_status():
    return jsonify({
        "module": "auth",
        "status": "ready"
    })


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    try:
        user_id = register_user(
            full_name=data.get("full_name", ""),
            email=data.get("email", ""),
            password=data.get("password", ""),
            role=data.get("role", "buyer"),
        )

        return jsonify({
            "success": True,
            "user_id": user_id
        }), 201

    except RegistrationError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400
