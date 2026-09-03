from flask import Flask, render_template
from database import init_database
from routes import auth

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

app.secret_key = "dz-market-secret-key-change-this-later"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ============================================================
# DATABASE
# ============================================================

init_database()


# ============================================================
# BLUEPRINTS
# ============================================================

app.register_blueprint(auth)


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():
    return {
        "status": "ok",
        "app": "DZ MARKET",
        "version": "1.0"
    }


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        "index.html"
    ), 404


@app.errorhandler(500)
def server_error(error):
    return """
    <h1>حدث خطأ في الخادم</h1>
    <p>DZ MARKET 🇩🇿</p>
    """, 500


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
