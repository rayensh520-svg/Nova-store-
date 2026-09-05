from app import create_app
from app.database import get_connection
from app.sellers.service import create_seller, create_store
from app.catalog.service import (
    create_product,
    create_category,
    assign_product_category,
    get_product_categories,
)


def setup_test_data():
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM users
            WHERE email = ?
            """,
            ("catalog.full.test@nova.local",),
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
                "NOVA Catalog Test Seller",
                "catalog.full.test@nova.local",
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
        name="NOVA Catalog Test Store",
        description="Full catalog test store.",
    )

    product_id = create_product(
        store_id=store_id,
        name="NOVA Test Product",
        description="Catalog test product.",
        price=2500,
        stock_quantity=15,
        fulfillment_type="ready_stock",
        owner_user_id=user_id,
    )

    category_id = create_category(
        name="Electronics",
        slug="electronics-test",
    )

    assign_product_category(
        product_id=product_id,
        category_id=category_id,
    )

    return (
        user_id,
        store_id,
        product_id,
        category_id,
    )


def test_catalog():
    (
        user_id,
        store_id,
        product_id,
        category_id,
    ) = setup_test_data()

    categories = get_product_categories(product_id)

    assert len(categories) == 1
    assert categories[0]["id"] == category_id
    assert categories[0]["slug"] == "electronics-test"

    app = create_app()
    app.config["TESTING"] = True

    client = app.test_client()

    response = client.get(
        f"/api/v1/catalog/products/{product_id}"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["product"]["id"] == product_id

    response = client.get(
        f"/api/v1/catalog/products/{product_id}/categories"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert len(data["categories"]) == 1
    assert data["categories"][0]["id"] == category_id

    response = client.get(
        "/api/v1/catalog/categories"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    found = any(
        category["id"] == category_id
        for category in data["categories"]
    )

    assert found is True

    print("NOVA CATALOG + CATEGORIES: OK")


if __name__ == "__main__":
    test_catalog()
