from flask import jsonify, request, session

from . import catalog_bp
from .models import Product
from .service import ProductError, create_product
from app.auth.guards import role_required
from app.database import get_connection


@catalog_bp.get("/products/<int:product_id>")
def get_product(product_id):
    product = Product.find_by_id(product_id)

    if product is None or not product.is_active:
        return jsonify({
            "success": False,
            "error": "Product not found."
        }), 404

    return jsonify({
        "success": True,
        "product": {
            "id": product.id,
            "store_id": product.store_id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock_quantity": product.stock_quantity,
            "fulfillment_type": product.fulfillment_type,
            "is_active": product.is_active
        }
    })


@catalog_bp.get("/stores/<int:store_id>/products")
def list_store_products(store_id):
    connection = get_connection()

    try:
        store = connection.execute(
            """
            SELECT id
            FROM stores
            WHERE id = ?
            AND is_visible = 1
            LIMIT 1
            """,
            (store_id,),
        ).fetchone()
    finally:
        connection.close()

    if store is None:
        return jsonify({
            "success": False,
            "error": "Store not found."
        }), 404

    products = Product.list_by_store(store_id)

    return jsonify({
        "success": True,
        "products": [
            {
                "id": product.id,
                "store_id": product.store_id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "fulfillment_type": product.fulfillment_type,
                "is_active": product.is_active
            }
            for product in products
        ]
    })


@catalog_bp.post("/stores/<int:store_id>/products")
@role_required("seller")
def create_store_product(store_id):
    data = request.get_json(silent=True) or {}

    try:
        product_id = create_product(
            store_id=store_id,
            name=data.get("name", ""),
            description=data.get("description", ""),
            price=data.get("price", 0),
            stock_quantity=data.get("stock_quantity", 0),
            fulfillment_type=data.get(
                "fulfillment_type",
                "ready_stock"
            ),
            owner_user_id=session["user_id"],
        )

        return jsonify({
            "success": True,
            "product_id": product_id
        }), 201

    except ProductError as error:
        error_message = str(error)

        if error_message == "Store not found.":
            status_code = 404
        elif error_message in {
            "You do not own this store.",
            "Seller account is inactive.",
            "Seller is not approved.",
        }:
            status_code = 403
        else:
            status_code = 400

        return jsonify({
            "success": False,
            "error": error_message
        }), status_code


@catalog_bp.patch("/products/<int:product_id>")
@role_required("seller")
def update_product(product_id):
    data = request.get_json(silent=True) or {}

    connection = get_connection()

    try:
        product = connection.execute(
            """
            SELECT
                products.id,
                products.store_id,
                sellers.user_id,
                sellers.is_active,
                sellers.verification_status
            FROM products
            JOIN stores
                ON stores.id = products.store_id
            JOIN sellers
                ON sellers.id = stores.seller_id
            WHERE products.id = ?
            LIMIT 1
            """,
            (product_id,),
        ).fetchone()

        if product is None:
            return jsonify({
                "success": False,
                "error": "Product not found."
            }), 404

        if product["user_id"] != session["user_id"]:
            return jsonify({
                "success": False,
                "error": "You do not own this product."
            }), 403

        if not product["is_active"]:
            return jsonify({
                "success": False,
                "error": "Seller account is inactive."
            }), 403

        if product["verification_status"] != "approved":
            return jsonify({
                "success": False,
                "error": "Seller is not approved."
            }), 403

        fields = []
        values = []

        if "name" in data:
            name = " ".join(
                str(data["name"]).split()
            )

            if not name or len(name) > 200:
                return jsonify({
                    "success": False,
                    "error": "Invalid product name."
                }), 400

            fields.append("name = ?")
            values.append(name)

        if "description" in data:
            description = " ".join(
                str(data["description"]).split()
            )

            if len(description) > 5000:
                return jsonify({
                    "success": False,
                    "error": "Product description is too long."
                }), 400

            fields.append("description = ?")
            values.append(description)

        if "price" in data:
            try:
                price = float(data["price"])
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "error": "Invalid product price."
                }), 400

            if price < 0:
                return jsonify({
                    "success": False,
                    "error": "Product price cannot be negative."
                }), 400

            fields.append("price = ?")
            values.append(price)

        if "stock_quantity" in data:
            try:
                stock = int(data["stock_quantity"])
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "error": "Invalid stock quantity."
                }), 400

            if stock < 0:
                return jsonify({
                    "success": False,
                    "error": "Stock quantity cannot be negative."
                }), 400

            fields.append("stock_quantity = ?")
            values.append(stock)

        if "fulfillment_type" in data:
            fulfillment_type = data["fulfillment_type"]

            if fulfillment_type not in {
                "ready_stock",
                "made_to_order",
            }:
                return jsonify({
                    "success": False,
                    "error": "Invalid fulfillment type."
                }), 400

            fields.append("fulfillment_type = ?")
            values.append(fulfillment_type)

        if not fields:
            return jsonify({
                "success": False,
                "error": "No valid fields to update."
            }), 400

        fields.append(
            "updated_at = CURRENT_TIMESTAMP"
        )

        values.append(product_id)

        connection.execute(
            f"""
            UPDATE products
            SET {", ".join(fields)}
            WHERE id = ?
            """,
            values,
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Product updated successfully."
        })

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


@catalog_bp.delete("/products/<int:product_id>")
@role_required("seller")
def deactivate_product(product_id):
    connection = get_connection()

    try:
        product = connection.execute(
            """
            SELECT
                products.id,
                sellers.user_id,
                sellers.is_active,
                sellers.verification_status
            FROM products
            JOIN stores
                ON stores.id = products.store_id
            JOIN sellers
                ON sellers.id = stores.seller_id
            WHERE products.id = ?
            LIMIT 1
            """,
            (product_id,),
        ).fetchone()

        if product is None:
            return jsonify({
                "success": False,
                "error": "Product not found."
            }), 404

        if product["user_id"] != session["user_id"]:
            return jsonify({
                "success": False,
                "error": "You do not own this product."
            }), 403

        if not product["is_active"]:
            return jsonify({
                "success": False,
                "error": "Seller account is inactive."
            }), 403

        if product["verification_status"] != "approved":
            return jsonify({
                "success": False,
                "error": "Seller is not approved."
            }), 403

        connection.execute(
            """
            UPDATE products
            SET
                is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (product_id,),
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Product deactivated successfully."
        })

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
@catalog_bp.get("/categories")
def list_categories():
    from .models import Category

    categories = Category.list_active()

    return jsonify({
        "success": True,
        "categories": [
            {
                "id": category.id,
                "parent_id": category.parent_id,
                "name": category.name,
                "slug": category.slug,
                "is_active": category.is_active
            }
            for category in categories
        ]
    })
