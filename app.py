import os

from flask import Flask, render_template

from database import init_database, init_app
from routes import auth


# ============================================================
# DZ MARKET 🇩🇿
# Flask Application
# ============================================================

app = Flask(__name__)


# ============================================================
# SECURITY / CONFIG
# ============================================================

app.secret_key = os.environ.get(
    "DZMARKET_SECRET_KEY",
    "change-this-secret-key-in-production"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# HTTPS production protection
if os.environ.get("DZMARKET_PRODUCTION") == "1":
    app.config["SESSION_COOKIE_SECURE"] = True
else:
    app.config["SESSION_COOKIE_SECURE"] = False


# ============================================================
# DATABASE
# ============================================================

init_app(app)
init_database()


# ============================================================
# BLUEPRINTS
# ============================================================

app.register_blueprint(auth)


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
# ERROR PAGES
# ============================================================

@app.errorhandler(403)
def forbidden(error):

    try:
        return render_template(
            "403.html"
        ), 403
    except Exception:
        return (
            "<h1>403 - Access denied</h1>",
            403
        )


@app.errorhandler(404)
def page_not_found(error):

    try:
        return render_template(
            "404.html"
        ), 404
    except Exception:
        return (
            "<h1>404 - Page not found</h1>",
            404
        )


@app.errorhandler(500)
def server_error(error):

    try:
        return render_template(
            "500.html"
        ), 500
    except Exception:
        return (
            "<h1>500 - Server error</h1>",
            500
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    debug_mode = (
        os.environ.get(
            "DZMARKET_DEBUG",
            "0"
        ) == "1"
    )

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=debug_mode
    )
