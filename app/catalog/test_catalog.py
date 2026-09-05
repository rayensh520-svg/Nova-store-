from app import create_app
from app.database import get_connection
from app.sellers.service import create_seller, create_store
from app.catalog.service import (
    create_product,
    create_category,
    assign_product_category,
    get_product_categories,
    add_product_media,
)


def setup_test_data():
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM users
            WHERE email = ?
            """,
            ("catalog.media.test@nova.local",),
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
                "NOVA Catalog Media Test Seller",
                "catalog.media.test@nova.local",
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
        name="NOVA Media Test Store",
        description="Media test store.",
    )

    product_id = create_product(
        store_id=store_id,
        name="NOVA Media Test Product",
        description="Product media test.",
        price=2500,
        stock_quantity=15,
        fulfillment_type="ready_stock",
        owner_user_id=user_id,
    )

    category_id = create_category(
        name="Media Test Category",
        slug=f"media-test-{product_id}",
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

    # Category service test
    categories = get_product_categories(product_id)

    assert len(categories) == 1
    assert categories[0]["id"] == category_id

    # Media service test
    media_id = add_product_media(
        product_id=product_id,
        media_type="image",
        storage_key=f"products/{product_id}/test-image.jpg",
        original_name="test-image.jpg",
        mime_type="image/jpeg",
        file_size=1024,
        sort_order=0,
        is_primary=True,
        owner_user_id=user_id,
    )

    assert media_id is not None

    # API application
    app = create_app()
    app.config["TESTING"] = True

    client = app.test_client()

    # Product API
    response = client.get(
        f"/api/v1/catalog/products/{product_id}"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["product"]["id"] == product_id

    # Categories API
    response = client.get(
        f"/api/v1/catalog/products/{product_id}/categories"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert len(data["categories"]) == 1
    assert data["categories"][0]["id"] == category_id

    # All categories API
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

    # Media API
    response = client.get(
        f"/api/v1/catalog/products/{product_id}/media"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert len(data["media"]) == 1
    assert data["media"][0]["id"] == media_id
    assert data["media"][0]["media_type"] == "image"
    assert data["media"][0]["is_primary"] is True

    print("NOVA CATALOG + CATEGORIES + MEDIA: OK")


if __name__ == "__main__":
    test_catalog()
