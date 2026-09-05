from app.database import get_connection


class ProductError(Exception):
    pass


VALID_FULFILLMENT_TYPES = {
    "ready_stock",
    "made_to_order",
}


def create_product(
    store_id: int,
    name: str,
    description: str = "",
    price=0,
    stock_quantity=0,
    fulfillment_type: str = "ready_stock",
    owner_user_id: int | None = None,
):
    name = " ".join(str(name).split())
    description = " ".join(str(description).split())

    if not name:
        raise ProductError("Product name is required.")

    if len(name) > 200:
        raise ProductError("Product name is too long.")

    if len(description) > 5000:
        raise ProductError("Product description is too long.")

    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ProductError("Invalid product price.")

    if price < 0:
        raise ProductError("Product price cannot be negative.")

    try:
        stock_quantity = int(stock_quantity)
    except (TypeError, ValueError):
        raise ProductError("Invalid stock quantity.")

    if stock_quantity < 0:
        raise ProductError(
            "Stock quantity cannot be negative."
        )

    if fulfillment_type not in VALID_FULFILLMENT_TYPES:
        raise ProductError(
            "Invalid fulfillment type."
        )

    connection = get_connection()

    try:
        store = connection.execute(
            """
            SELECT
                stores.id,
                sellers.user_id,
                sellers.is_active,
                sellers.verification_status
            FROM stores
            JOIN sellers
                ON sellers.id = stores.seller_id
            WHERE stores.id = ?
            LIMIT 1
            """,
            (store_id,),
        ).fetchone()

        if store is None:
            raise ProductError("Store not found.")

        if owner_user_id is not None:
            if store["user_id"] != owner_user_id:
                raise ProductError(
                    "You do not own this store."
                )

        if not store["is_active"]:
            raise ProductError(
                "Seller account is inactive."
            )

        if store["verification_status"] != "approved":
            raise ProductError(
                "Seller is not approved."
            )

        cursor = connection.execute(
            """
            INSERT INTO products (
                store_id,
                name,
                description,
                price,
                stock_quantity,
                fulfillment_type
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                store_id,
                name,
                description,
                price,
                stock_quantity,
                fulfillment_type,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
