from flask import jsonify, request, session

from . import auth_bp
from .service import (
    LoginError,
    RegistrationError,
    login_user,
    register_user,
)


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


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    try:
        user = login_user(
            email=data.get("email", ""),
            password=data.get("password", ""),
        )

        session.clear()

        session["user_id"] = user["id"]
        session["user_role"] = user["role"]

        return jsonify({
            "success": True,
            "user": user
        })

    except LoginError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 401
