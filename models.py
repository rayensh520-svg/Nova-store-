import sqlite3
from database import get_connection


class User:
    @staticmethod
    def create(full_name, email, password, role="buyer"):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO users (full_name, email, password, role)
                VALUES (?, ?, ?, ?)
                """,
                (full_name, email, password, role)
            )

            connection.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            return None

        finally:
            connection.close()

    @staticmethod
    def find_by_email(email):
        connection = get_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        connection.close()
        return user

    @staticmethod
    def find_by_id(user_id):
        connection = get_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        connection.close()
        return user


class Product:
    @staticmethod
    def create(
        store_id,
        name,
        description="",
        price=0,
        quantity=0,
        category="",
        image=""
    ):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO products
            (
                store_id,
                name,
                description,
                price,
                quantity,
                category,
                image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                store_id,
                name,
                description,
                price,
                quantity,
                category,
                image
            )
        )

        connection.commit()
        product_id = cursor.lastrowid
        connection.close()

        return product_id

    @staticmethod
    def all():
        connection = get_connection()

        products = connection.execute(
            """
            SELECT *
            FROM products
            ORDER BY created_at DESC
            """
        ).fetchall()

        connection.close()
        return products

    @staticmethod
    def find_by_id(product_id):
        connection = get_connection()

        product = connection.execute(
            """
            SELECT *
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        ).fetchone()

        connection.close()
        return product


class Store:
    @staticmethod
    def create(user_id, name, description="", phone="", wilaya=""):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO stores
            (
                user_id,
                name,
                description,
                phone,
                wilaya
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                description,
                phone,
                wilaya
            )
        )

        connection.commit()
        store_id = cursor.lastrowid
        connection.close()

        return store_id

    @staticmethod
    def find_by_user_id(user_id):
        connection = get_connection()

        store = connection.execute(
            """
            SELECT *
            FROM stores
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        connection.close()
        return store


class Favorite:
    @staticmethod
    def add(user_id, product_id):
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO favorites (user_id, product_id)
                VALUES (?, ?)
                """,
                (user_id, product_id)
            )

            connection.commit()
            return True

        except sqlite3.IntegrityError:
            return False

        finally:
            connection.close()

    @staticmethod
    def remove(user_id, product_id):
        connection = get_connection()

        connection.execute(
            """
            DELETE FROM favorites
            WHERE user_id = ?
            AND product_id = ?
            """,
            (user_id, product_id)
        )

        connection.commit()
        connection.close()


class Cart:
    @staticmethod
    def add(user_id, product_id, quantity=1):
        connection = get_connection()

        existing = connection.execute(
            """
            SELECT id, quantity
            FROM cart_items
            WHERE user_id = ?
            AND product_id = ?
            """,
            (user_id, product_id)
        ).fetchone()

        if existing:
            connection.execute(
                """
                UPDATE cart_items
                SET quantity = quantity + ?
                WHERE id = ?
                """,
                (quantity, existing["id"])
            )
        else:
            connection.execute(
                """
                INSERT INTO cart_items
                (user_id, product_id, quantity)
                VALUES (?, ?, ?)
                """,
                (user_id, product_id, quantity)
            )

        connection.commit()
        connection.close()

    @staticmethod
    def get_items(user_id):
        connection = get_connection()

        items = connection.execute(
            """
            SELECT
                cart_items.id,
                cart_items.quantity,
                products.name,
                products.price,
                products.image
            FROM cart_items
            JOIN products
                ON products.id = cart_items.product_id
            WHERE cart_items.user_id = ?
            ORDER BY cart_items.created_at DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()
        return items


class Order:
    @staticmethod
    def create(user_id, total, delivery_address=""):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO orders
            (
                user_id,
                total,
                delivery_address
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                total,
                delivery_address
            )
        )

        connection.commit()
        order_id = cursor.lastrowid
        connection.close()

        return order_id


class Complaint:
    @staticmethod
    def create(user_id, subject, message):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO complaints
            (
                user_id,
                subject,
                message
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                subject,
                message
            )
        )

        connection.commit()
        complaint_id = cursor.lastrowid
        connection.close()

        return complaint_id
