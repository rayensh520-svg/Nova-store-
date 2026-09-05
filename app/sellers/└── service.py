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


def create_store(
    seller_id: int,
    name: str,
    description: str = "",
):
    name = " ".join(name.split())
    description = " ".join(description.split())

    if not name:
        raise SellerError("Store name is required.")

    if len(name) > 120:
        raise SellerError("Store name is too long.")

    if len(description) > 2000:
        raise SellerError("Store description is too long.")

    connection = get_connection()

    try:
        seller = connection.execute(
            """
            SELECT id
            FROM sellers
            WHERE id = ?
            LIMIT 1
            """,
            (seller_id,),
        ).fetchone()

        if seller is None:
            raise SellerError("Seller not found.")

        existing_store = connection.execute(
            """
            SELECT id
            FROM stores
            WHERE seller_id = ?
            LIMIT 1
            """,
            (seller_id,),
        ).fetchone()

        if existing_store is not None:
            raise SellerError(
                "This seller already has a store."
            )

        cursor = connection.execute(
            """
            INSERT INTO stores (
                seller_id,
                name,
                description
            )
            VALUES (?, ?, ?)
            """,
            (
                seller_id,
                name,
                description,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()
