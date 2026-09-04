from flask import Flask, render_template, jsonify, request
from database import init_db

app = Flask(__name__)

app.config["JSON_SORT_KEYS"] = False

# ==============================
# DATABASE INITIALIZATION
# ==============================
try:
    init_db()
    print("VYORA database initialized successfully.")
except Exception as e:
    print(f"Database initialization error: {e}")


# ==============================
# PUBLIC PAGES
# ==============================

@app.route("/")
def index():
    return render_template("splash.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/categories")
def categories():
    return render_template("categories.html")


@app.route("/product/<int:product_id>")
def product(product_id):
    return render_template(
        "product.html",
        product=None,
        product_id=product_id
    )


@app.route("/cart")
def cart():
    return render_template("cart.html", cart=[])


@app.route("/checkout")
def checkout():
    return render_template("checkout.html", cart=[])


@app.route("/favorites")
def favorites():
    return render_template("favorites.html")


@app.route("/profile")
def profile():
    return render_template("profile.html")


@app.route("/notifications")
def notifications():
    return render_template("notifications.html")


@app.route("/orders")
def orders():
    return render_template("orders.html")


@app.route("/order/<int:order_id>")
def buyer_order_details(order_id):
    return render_template(
        "order_details.html",
        order=None,
        order_id=order_id
    )


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/ai-assistant")
def ai_assistant():
    return render_template("ai_assistant.html")


# ==============================
# SELLER PAGES
# ==============================

@app.route("/seller")
def seller():
    return render_template("seller.html")


@app.route("/seller/dashboard")
def seller_dashboard():
    return render_template("seller_dashboard.html")


@app.route("/seller/products")
def seller_products():
    return render_template("seller_products.html")


@app.route("/seller/products/add")
def add_product():
    return render_template("add_product.html")


@app.route("/seller/products/<int:product_id>/edit")
def edit_product(product_id):
    return render_template(
        "edit_product.html",
        product=None,
        product_id=product_id
    )


@app.route("/seller/orders")
def seller_orders():
    return render_template("seller_orders.html")


@app.route("/seller/orders/<int:order_id>")
def seller_order_details(order_id):
    return render_template(
        "order_details.html",
        order=None,
        order_id=order_id
    )


@app.route("/seller/wallet")
def seller_wallet():
    return render_template("seller_wallet.html")


@app.route("/seller/analytics")
def seller_analytics():
    return render_template("seller_analytics.html")


@app.route("/seller/settings")
def seller_settings():
    return render_template("seller_settings.html")


@app.route("/seller/<int:seller_id>")
def seller_store(seller_id):
    return render_template(
        "seller_store.html",
        seller=None,
        products=[],
        seller_id=seller_id
    )


# ==============================
# API
# ==============================

@app.route("/api/health")
def health():
    return jsonify({
        "success": True,
        "app": "VYORA STORE",
        "status": "running"
    })


@app.route("/api/status")
def api_status():
    return jsonify({
        "success": True,
        "environment": "development",
        "database": "connected",
        "authentication": "not_connected",
        "message": "VYORA backend is ready for authentication integration."
    })


@app.route("/api/test", methods=["GET"])
def api_test():
    return jsonify({
        "success": True,
        "message": "VYORA API is working."
    })


@app.route("/api/test", methods=["POST"])
def api_test_post():
    data = request.get_json(silent=True) or {}

    return jsonify({
        "success": True,
        "received": data
    })


# ==============================
# ERROR HANDLERS
# ==============================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Page not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "Method not allowed"
    }), 405


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ==============================
# START SERVER
# ==============================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
)
