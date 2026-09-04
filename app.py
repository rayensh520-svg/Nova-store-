from flask import Flask, render_template, jsonify, request, session
from database import init_db
from auth import register_user, login_user, logout_user, seller_required

import sqlite3
import os
from decimal import Decimal, InvalidOperation


app = Flask(__name__)

app.config["JSON_SORT_KEYS"] = False

app.config["SECRET_KEY"] = os.environ.get(
    "VYORA_SECRET_KEY",
    "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY"
)


# =========================================================
# DATABASE
# =========================================================

DATABASE = "data/vyora.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def row_to_dict(row):
    if row is None:
        return None

    return dict(row)


# =========================================================
# STARTUP
# =========================================================

try:
    init_db()
    print("VYORA database initialized successfully.")
except Exception as error:
    print(f"Database initialization error: {error}")


# =========================================================
# PUBLIC PAGES
# =========================================================

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
    return render_template(
        "cart.html",
        cart=[]
    )


@app.route("/checkout")
def checkout():
    return render_template(
        "checkout.html",
        cart=[]
    )


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


# =========================================================
# SELLER PAGES
# =========================================================

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


# =========================================================
# AUTH API
# =========================================================

@app.route("/api/auth/register", methods=["POST"])
def api_register():

    data = request.get_json(silent=True) or {}

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "buyer")

    success, result = register_user(
        full_name,
        email,
        password,
        role
    )

    if not success:

        return jsonify({
            "success": False,
            "error": result
        }), 400


    session["user_id"] = result["user_id"]
    session["user_role"] = result["role"]
    session["user_name"] = result["full_name"]


    return jsonify({

        "success": True,

        "message":
            "Account created successfully.",

        "user": {

            "id":
                result["user_id"],

            "name":
                result["full_name"],

            "email":
                result["email"],

            "role":
                result["role"]

        }

    }), 201


@app.route("/api/auth/login", methods=["POST"])
def api_login():

    data = request.get_json(silent=True) or {}

    email = data.get("email")
    password = data.get("password")


    success, result = login_user(
        email,
        password
    )


    if not success:

        return jsonify({

            "success": False,

            "error": result

        }), 401


    return jsonify({

        "success": True,

        "message":
            "Login successful.",

        "user": {

            "id":
                result["user_id"],

            "name":
                result["full_name"],

            "email":
                result["email"],

            "role":
                result["role"]

        }

    })


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():

    logout_user()

    return jsonify({

        "success": True,

        "message":
            "Logged out successfully."

    })


@app.route("/api/auth/me", methods=["GET"])
def api_current_user():

    if "user_id" not in session:

        return jsonify({

            "success": False,

            "authenticated": False

        }), 401


    return jsonify({

        "success": True,

        "authenticated": True,

        "user": {

            "id":
                session["user_id"],

            "name":
                session.get("user_name"),

            "role":
                session.get("user_role")

        }

    })


# =========================================================
# SELLER PRODUCT HELPERS
# =========================================================

def get_current_seller():

    user_id = session.get("user_id")

    if not user_id:
        return None


    connection = get_connection()

    try:

        seller = connection.execute(
            """
            SELECT
                s.id,
                s.user_id,
                st.id AS store_id
            FROM sellers s
            LEFT JOIN stores st
                ON st.seller_id = s.id
            WHERE s.user_id = ?
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()


        return seller

    finally:

        connection.close()


def validate_product_data(data):

    name = str(
        data.get("name") or ""
    ).strip()

    description = str(
        data.get("description") or ""
    ).strip()

    category = str(
        data.get("category") or ""
    ).strip()

    delivery_info = str(
        data.get("delivery_info") or ""
    ).strip()

    availability_mode = str(
        data.get("availability_mode")
        or "in_stock"
    ).strip()

    visibility = str(
        data.get("visibility")
        or data.get("status")
        or "active"
    ).strip()


    if not name:

        return False, "اسم المنتج مطلوب."


    if len(name) > 150:

        return False, "اسم المنتج طويل جدًا."


    if len(description) > 5000:

        return False, "وصف المنتج طويل جدًا."


    if not category:

        return False, "فئة المنتج مطلوبة."


    try:

        price = Decimal(
            str(data.get("price"))
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError
    ):

        return False, "السعر غير صالح."


    if price < 0:

        return False, "السعر لا يمكن أن يكون سالبًا."


    if availability_mode not in (
        "in_stock",
        "made_to_order"
    ):

        return False, "طريقة التوفر غير صالحة."


    quantity = None


    if availability_mode == "in_stock":

        try:

            quantity = int(
                data.get("quantity")
            )

        except (
            TypeError,
            ValueError
        ):

            return False, "الكمية غير صالحة."


        if quantity < 0:

            return False, "الكمية لا يمكن أن تكون سالبة."


    if visibility not in (
        "active",
        "hidden"
    ):

        return False, "حالة المنتج غير صالحة."


    return True, {

        "name":
            name,

        "description":
            description,

        "category":
            category,

        "price":
            str(price),

        "availability_mode":
            availability_mode,

        "quantity":
            quantity,

        "delivery_info":
            delivery_info,

        "status":
            visibility

    }


# =========================================================
# SELLER PRODUCTS API
# =========================================================

@app.route(
    "/api/seller/products",
    methods=["GET"]
)
@seller_required
def api_seller_products():

    seller = get_current_seller()


    if not seller:

        return jsonify({

            "success": False,

            "error":
                "Seller profile not found."

        }), 404


    store_id = seller["store_id"]


    if not store_id:

        return jsonify({

            "success": True,

            "products": []

        })


    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM products
            WHERE store_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (store_id,)
        ).fetchall()


        products = []

        for row in rows:

            item = row_to_dict(row)

            products.append(item)


        return jsonify({

            "success": True,

            "products": products

        })


    finally:

        connection.close()


@app.route(
    "/api/seller/products",
    methods=["POST"]
)
@seller_required
def api_create_product():

    seller = get_current_seller()


    if not seller:

        return jsonify({

            "success": False,

            "error":
                "Seller profile not found."

        }), 404


    if not seller["store_id"]:

        return jsonify({

            "success": False,

            "error":
                "Create your store before adding products."

        }), 400


    data = request.get_json(silent=True) or {}


    valid, result = validate_product_data(data)


    if not valid:

        return jsonify({

            "success": False,

            "error": result

        }), 400


    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            INSERT INTO products
            (
                store_id,
                name,
                description,
                category,
                price,
                availability_mode,
                quantity,
                delivery_info,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                seller["store_id"],
                result["name"],
                result["description"],
                result["category"],
                result["price"],
                result["availability_mode"],
                result["quantity"],
                result["delivery_info"],
                result["status"]
            )
        )


        connection.commit()


        product_id = cursor.lastrowid


        product = connection.execute(
            """
            SELECT *
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        ).fetchone()


        return jsonify({

            "success": True,

            "message":
                "Product created successfully.",

            "product":
                row_to_dict(product)

        }), 201


    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({

            "success": False,

            "error":
                f"Database error: {error}"

        }), 500

    finally:

        connection.close()


@app.route(
    "/api/seller/products/<int:product_id>",
    methods=["GET"]
)
@seller_required
def api_get_seller_product(product_id):

    seller = get_current_seller()


    if not seller or not seller["store_id"]:

        return jsonify({

            "success": False,

            "error":
                "Seller store not found."

        }), 404


    connection = get_connection()

    try:

        product = connection.execute(
            """
            SELECT *
            FROM products
            WHERE id = ?
              AND store_id = ?
            LIMIT 1
            """,
            (
                product_id,
                seller["store_id"]
            )
        ).fetchone()


        if not product:

            return jsonify({

                "success": False,

                "error":
                    "Product not found."

            }), 404


        return jsonify({

            "success": True,

            "product":
                row_to_dict(product)

        })


    finally:

        connection.close()


@app.route(
    "/api/seller/products/<int:product_id>",
    methods=["PUT"]
)
@seller_required
def api_update_product(product_id):

    seller = get_current_seller()


    if not seller or not seller["store_id"]:

        return jsonify({

            "success": False,

            "error":
                "Seller store not found."

        }), 404


    data = request.get_json(silent=True) or {}


    valid, result = validate_product_data(data)


    if not valid:

        return jsonify({

            "success": False,

            "error": result

        }), 400


    connection = get_connection()

    try:

        existing = connection.execute(
            """
            SELECT id
            FROM products
            WHERE id = ?
              AND store_id = ?
            LIMIT 1
            """,
            (
                product_id,
                seller["store_id"]
            )
        ).fetchone()


        if not existing:

            return jsonify({

                "success": False,

                "error":
                    "Product not found."

            }), 404


        connection.execute(
            """
            UPDATE products
            SET
                name = ?,
                description = ?,
                category = ?,
                price = ?,
                availability_mode = ?,
                quantity = ?,
                delivery_info = ?,
                status = ?
            WHERE id = ?
              AND store_id = ?
            """,
            (
                result["name"],
                result["description"],
                result["category"],
                result["price"],
                result["availability_mode"],
                result["quantity"],
                result["delivery_info"],
                result["status"],
                product_id,
                seller["store_id"]
            )
        )


        connection.commit()


        updated = connection.execute(
            """
            SELECT *
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        ).fetchone()


        return jsonify({

            "success": True,

            "message":
                "Product updated successfully.",

            "product":
                row_to_dict(updated)

        })


    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({

            "success": False,

            "error":
                f"Database error: {error}"

        }), 500

    finally:

        connection.close()


@app.route(
    "/api/seller/products/<int:product_id>",
    methods=["DELETE"]
)
@seller_required
def api_delete_product(product_id):

    seller = get_current_seller()


    if not seller or not seller["store_id"]:

        return jsonify({

            "success": False,

            "error":
                "Seller store not found."

        }), 404


    connection = get_connection()

    try:

        existing = connection.execute(
            """
            SELECT id
            FROM products
            WHERE id = ?
              AND store_id = ?
            LIMIT 1
            """,
            (
                product_id,
                seller["store_id"]
            )
        ).fetchone()


        if not existing:

            return jsonify({

                "success": False,

                "error":
                    "Product not found."

            }), 404


        connection.execute(
            """
            DELETE FROM products
            WHERE id = ?
              AND store_id = ?
            """,
            (
                product_id,
                seller["store_id"]
            )
        )


        connection.commit()


        return jsonify({

            "success": True,

            "message":
                "Product deleted successfully."

        })


    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({

            "success": False,

            "error":
                f"Database error: {error}"

        }), 500

    finally:

        connection.close()


# =========================================================
# HEALTH / STATUS
# =========================================================

@app.route("/api/health")
def health():

    return jsonify({

        "success": True,

        "app":
            "VYORA STORE",

        "status":
            "running"

    })


@app.route("/api/status")
def api_status():

    return jsonify({

        "success": True,

        "environment":
            "development",

        "database":
            "connected",

        "authentication":
            "connected",

        "products_api":
            "connected",

        "message":
            "VYORA backend is connected."

    })


@app.route("/api/test", methods=["GET"])
def api_test():

    return jsonify({

        "success": True,

        "message":
            "VYORA API is working."

    })


@app.route("/api/test", methods=["POST"])
def api_test_post():

    data = request.get_json(
        silent=True
    ) or {}


    return jsonify({

        "success": True,

        "received":
            data

    })


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "success": False,

        "error":
            "Page not found"

    }), 404


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "success": False,

        "error":
            "Method not allowed"

    }), 405


@app.errorhandler(500)
def server_error(error):

    return jsonify({

        "success": False,

        "error":
            "Internal server error"

    }), 500


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )
