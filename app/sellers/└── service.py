from app.database import get_connection


class SellerError(Exception):
    pass


def create_seller(user_id: int):
    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT id, role
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        if user is None:
            raise SellerError("User not found.")

        if user["role"] != "seller":
            raise SellerError("User is not a seller.")

        existing_seller = connection.execute(
            """
            SELECT id
            FROM sellers
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        if existing_seller is not None:
            return existing_seller["id"]

        cursor = connection.execute(
            """
            INSERT INTO sellers (user_id)
            VALUES (?)
            """,
            (user_id,),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()
