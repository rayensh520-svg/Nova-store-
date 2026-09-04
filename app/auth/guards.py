from functools import wraps

from flask import jsonify, session


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            return jsonify({
                "success": False,
                "error": "Authentication required."
            }), 401

        return view(*args, **kwargs)

    return wrapped_view


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user_id = session.get("user_id")
            user_role = session.get("user_role")

            if not user_id:
                return jsonify({
                    "success": False,
                    "error": "Authentication required."
                }), 401

            if user_role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "error": "Permission denied."
                }), 403

            return view(*args, **kwargs)

        return wrapped_view

    return decorator
