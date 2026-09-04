from flask import Flask, jsonify, render_template

app = Flask(__name__)

# ============================================================
# VYORA STORE
# Main application entry point
# ============================================================

app.config["JSON_SORT_KEYS"] = False


# ============================================================
# BASIC PAGES
# ============================================================

@app.route("/")
def index():
    return render_template("splash.html")


@app.route("/home")
def home():
    return render_template("home.html")


# ============================================================
# HEALTH CHECK
# Used to verify that the server is running correctly.
# ============================================================

@app.route("/api/health")
def health():
    return jsonify({
        "success": True,
        "app": "VYORA STORE",
        "status": "running"
    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Page not found"
    }), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )
