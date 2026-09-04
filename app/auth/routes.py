from flask import jsonify

from . import auth_bp

@auth_bp.get("/status")
def auth_status():
return jsonify({
"module": "auth",
"status": "ready"
})
