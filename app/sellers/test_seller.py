from app.database import get_connection
from app.sellers.service import create_seller, create_store


def test_seller_store():
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM users
            WHERE email = ?
            """,
            ("seller.test@nova.local",),
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
                "NOVA Test Seller",
                "seller.test@nova.local",
                "test-password-hash",
                "seller",
            ),
        )

        user_id = cursor.lastrowid

        connection.commit()

        seller_id = create_seller(user_id)

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
        name="NOVA Test Store",
        description="Test seller store.",
    )

    assert seller_id is not None
    assert store_id is not None

    print("NOVA SELLER & STORE: OK")


if __name__ == "__main__":
    test_seller_store()
