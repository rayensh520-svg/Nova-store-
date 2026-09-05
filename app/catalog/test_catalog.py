from app.database import get_connection
from app.sellers.service import create_seller, create_store
from app.catalog.service import create_product
from app.catalog.models import Product


def test_catalog():
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM users
            WHERE email = ?
            """,
            ("catalog.test@nova.local",),
        )
        connection.commit()

        cursor = connection.execute(
            """
            INSERT INTO users (
                full_name,
                email,
                password_hash,
                role
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "NOVA Catalog Seller",
                "catalog.test@nova.local",
                "test-password-hash",
                "seller",
            ),
        )

        user_id = cursor.lastrowid
        connection.commit()

    finally:
        connection.close()

    seller_id = create_seller(user_id)

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE sellers
            SET verification_status = 'approved'
            WHERE id = ?
            """,
            (seller_id,),
        )
        connection.commit()

    finally:
        connection.close()

    store_id = create_store(
        seller_id=seller_id,
        name="NOVA Catalog Store",
        description="Catalog test store.",
    )

    product_id = create_product(
        store_id=store_id,
        name="NOVA Test Product",
        description="Test product.",
        price=1500,
        stock_quantity=10,
        fulfillment_type="ready_stock",
    )

    product = Product.find_by_id(product_id)

    assert seller_id is not None
    assert store_id is not None
    assert product_id is not None

    assert product is not None
    assert product.name == "NOVA Test Product"
    assert product.price == 1500
    assert product.stock_quantity == 10
    assert product.fulfillment_type == "ready_stock"
    assert product.is_active is True

    products = Product.list_by_store(store_id)

    assert len(products) == 1
    assert products[0].id == product_id

    print("NOVA CATALOG & PRODUCTS: OK")


if __name__ == "__main__":
    test_catalog()
