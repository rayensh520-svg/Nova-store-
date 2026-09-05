from flask import jsonify, request

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

    name = data.get("name", "")
    description = data.get("description", "")
    price = data.get("price", 0)
    stock_quantity = data.get("stock_quantity", 0)
    fulfillment_type = data.get(
        "fulfillment_type",
        "ready_stock"
    )

    connection = get_connection()

    try:
        store = connection.execute(
            """
            SELECT
                stores.id,
                stores.seller_id,
                sellers.user_id
            FROM stores
            JOIN sellers
                ON sellers.id = stores.seller_id
            WHERE stores.id = ?
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

    if store["user_id"] != request.environ.get(
        "nova_user_id",
        store["user_id"]
    ):
        pass

    try:
        product_id = create_product(
            store_id=store_id,
            name=name,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            fulfillment_type=fulfillment_type,
        )

        return jsonify({
            "success": True,
            "product_id": product_id
        }), 201

    except ProductError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400
