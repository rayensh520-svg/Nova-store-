from app import create_app
from app.database import get_connection
from app.sellers.service import create_seller, create_store
from app.catalog.service import create_product


def setup_test_data():
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM users
            WHERE email = ?
            """,
            ("catalog.api.test@nova.local",),
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
                "NOVA API Test Seller",
                "catalog.api.test@nova.local",
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
        name="NOVA API Test Store",
        description="API test store.",
    )

    product_id = create_product(
        store_id=store_id,
        name="NOVA API Product",
        description="Product created for API testing.",
        price=2500,
        stock_quantity=15,
        fulfillment_type="ready_stock",
        owner_user_id=user_id,
    )

    return user_id, store_id, product_id


def test_catalog_api():
    app = create_app()
    app.config["TESTING"] = True

    user_id, store_id, product_id = setup_test_data()

    client = app.test_client()

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["user_role"] = "seller"

    response = client.get(
        f"/api/v1/catalog/products/{product_id}"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["product"]["id"] == product_id
    assert data["product"]["name"] == "NOVA API Product"
    assert data["product"]["price"] == 2500
    assert data["product"]["stock_quantity"] == 15

    response = client.get(
        f"/api/v1/catalog/stores/{store_id}/products"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert len(data["products"]) >= 1

    found_product = next(
        product
        for product in data["products"]
        if product["id"] == product_id
    )

    assert found_product["name"] == "NOVA API Product"

    print("NOVA CATALOG API: OK")


if __name__ == "__main__":
    test_catalog_api()
