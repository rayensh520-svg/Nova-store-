import sqlite3
from database import get_connection


# =========================================================
# USER
# =========================================================

class User:

    @staticmethod
    def create(
        full_name,
        email,
        password,
        role="buyer",
        phone="",
        profile_image=""
    ):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO users
                (
                    full_name,
                    email,
                    password,
                    role,
                    phone,
                    profile_image
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    full_name,
                    email,
                    password,
                    role,
                    phone,
                    profile_image
                )
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
            WHERE LOWER(email) = LOWER(?)
            LIMIT 1
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
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

        connection.close()
        return user

    @staticmethod
    def update_profile(
        user_id,
        full_name=None,
        phone=None,
        profile_image=None
    ):
        connection = get_connection()

        fields = []
        values = []

        if full_name is not None:
            fields.append("full_name = ?")
            values.append(full_name)

        if phone is not None:
            fields.append("phone = ?")
            values.append(phone)

        if profile_image is not None:
            fields.append("profile_image = ?")
            values.append(profile_image)

        if fields:
            values.append(user_id)

            connection.execute(
                f"""
                UPDATE users
                SET {", ".join(fields)}
                WHERE id = ?
                """,
                values
            )

            connection.commit()

        connection.close()

    @staticmethod
    def update_settings(
        user_id,
        language=None,
        dark_mode=None,
        notifications_enabled=None
    ):
        connection = get_connection()

        fields = []
        values = []

        if language is not None:
            fields.append("language = ?")
            values.append(language)

        if dark_mode is not None:
            fields.append("dark_mode = ?")
            values.append(int(bool(dark_mode)))

        if notifications_enabled is not None:
            fields.append("notifications_enabled = ?")
            values.append(int(bool(notifications_enabled)))

        if fields:
            values.append(user_id)

            connection.execute(
                f"""
                UPDATE users
                SET {", ".join(fields)}
                WHERE id = ?
                """,
                values
            )

            connection.commit()

        connection.close()

    @staticmethod
    def verify_phone(user_id):
        connection = get_connection()

        connection.execute(
            """
            UPDATE users
            SET phone_verified = 1
            WHERE id = ?
            """,
            (user_id,)
        )

        connection.commit()
        connection.close()


# =========================================================
# STORE
# =========================================================

class Store:

    @staticmethod
    def create(
        user_id,
        name,
        description="",
        phone="",
        wilaya="",
        municipality=""
    ):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO stores
                (
                    user_id,
                    name,
                    description,
                    phone,
                    wilaya,
                    municipality
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    description,
                    phone,
                    wilaya,
                    municipality
                )
            )

            connection.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            return None

        finally:
            connection.close()

    @staticmethod
    def find_by_user_id(user_id):
        connection = get_connection()

        store = connection.execute(
            """
            SELECT *
            FROM stores
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

        connection.close()
        return store

    @staticmethod
    def find_by_id(store_id):
        connection = get_connection()

        store = connection.execute(
            """
            SELECT *
            FROM stores
            WHERE id = ?
            LIMIT 1
            """,
            (store_id,)
        ).fetchone()

        connection.close()
        return store

    @staticmethod
    def update(
        store_id,
        name=None,
        description=None,
        phone=None,
        wilaya=None,
        municipality=None,
        logo=None,
        cover_image=None,
        opening_hours=None
    ):
        connection = get_connection()

        fields = []
        values = []

        data = {
            "name": name,
            "description": description,
            "phone": phone,
            "wilaya": wilaya,
            "municipality": municipality,
            "logo": logo,
            "cover_image": cover_image,
            "opening_hours": opening_hours
        }

        for field, value in data.items():
            if value is not None:
                fields.append(f"{field} = ?")
                values.append(value)

        if fields:
            values.append(store_id)

            connection.execute(
                f"""
                UPDATE stores
                SET {", ".join(fields)}
                WHERE id = ?
                """,
                values
            )

            connection.commit()

        connection.close()

    @staticmethod
    def public_profile(store_id):
        connection = get_connection()

        store = connection.execute(
            """
            SELECT
                s.*,
                u.full_name,
                u.role,
                u.seller_verification_status
            FROM stores s
            JOIN users u ON u.id = s.user_id
            WHERE s.id = ?
            LIMIT 1
            """,
            (store_id,)
        ).fetchone()

        connection.close()
        return store

    @staticmethod
    def increment_sales(store_id):
        connection = get_connection()

        connection.execute(
            """
            UPDATE stores
            SET sales_count = COALESCE(sales_count, 0) + 1
            WHERE id = ?
            """,
            (store_id,)
        )

        connection.commit()
        connection.close()

    @staticmethod
    def update_trust_score(store_id, score):
        score = max(0, min(100, float(score)))

        connection = get_connection()

        connection.execute(
            """
            UPDATE stores
            SET trust_score = ?
            WHERE id = ?
            """,
            (score, store_id)
        )

        connection.commit()
        connection.close()


# =========================================================
# PRODUCT
# =========================================================

class Product:

    @staticmethod
    def create(
        store_id,
        name,
        description="",
        brand_name="",
        brand_logo="",
        price=0,
        old_price=None,
        discount_percent=0,
        quantity=0,
        category="",
        image="",
        video="",
        is_algerian=0,
        delivery_wilayas=""
    ):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO products
                (
                    store_id,
                    name,
                    description,
                    brand_name,
                    brand_logo,
                    price,
                    old_price,
                    discount_percent,
                    quantity,
                    category,
                    image,
                    video,
                    is_algerian,
                    delivery_wilayas
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    store_id,
                    name,
                    description,
                    brand_name,
                    brand_logo,
                    price,
                    old_price,
                    discount_percent,
                    quantity,
                    category,
                    image,
                    video,
                    int(bool(is_algerian)),
                    delivery_wilayas
                )
            )

            connection.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            return None

        finally:
            connection.close()

    @staticmethod
    def find_by_id(product_id):
        connection = get_connection()

        product = connection.execute(
            """
            SELECT
                p.*,
                s.name AS store_name,
                s.logo AS store_logo,
                s.wilaya AS store_wilaya,
                s.trust_score,
                u.seller_verification_status
            FROM products p
            JOIN stores s ON s.id = p.store_id
            JOIN users u ON u.id = s.user_id
            WHERE p.id = ?
            LIMIT 1
            """,
            (product_id,)
        ).fetchone()

        connection.close()
        return product

    @staticmethod
    def by_store(store_id):
        connection = get_connection()

        products = connection.execute(
            """
            SELECT *
            FROM products
            WHERE store_id = ?
            AND is_active = 1
            ORDER BY created_at DESC
            """,
            (store_id,)
        ).fetchall()

        connection.close()
        return products

    @staticmethod
    def update_rating(product_id):
        connection = get_connection()

        result = connection.execute(
            """
            SELECT
                AVG(rating) AS average_rating,
                COUNT(*) AS review_count
            FROM reviews
            WHERE product_id = ?
            """,
            (product_id,)
        ).fetchone()

        connection.execute(
            """
            UPDATE products
            SET
                rating = COALESCE(?, 0),
                reviews_count = COALESCE(?, 0)
            WHERE id = ?
            """,
            (
                result["average_rating"],
                result["review_count"],
                product_id
            )
        )

        connection.commit()
        connection.close()


# =========================================================
# FAVORITES
# =========================================================

class Favorite:

    @staticmethod
    def add(user_id, product_id):
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO favorites
                (user_id, product_id)
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

    @staticmethod
    def all(user_id):
        connection = get_connection()

        rows = connection.execute(
            """
            SELECT p.*
            FROM favorites f
            JOIN products p ON p.id = f.product_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()
        return rows


# =========================================================
# CART
# =========================================================

class Cart:

    @staticmethod
    def add(user_id, product_id, quantity=1):
        connection = get_connection()

        connection.execute(
            """
            INSERT INTO cart_items
            (user_id, product_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id)
            DO UPDATE SET quantity = quantity + excluded.quantity
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
                c.*,
                p.name,
                p.price,
                p.image,
                p.quantity AS stock_quantity
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = ?
            ORDER BY c.created_at DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()
        return items

    @staticmethod
    def remove(user_id, product_id):
        connection = get_connection()

        connection.execute(
            """
            DELETE FROM cart_items
            WHERE user_id = ?
            AND product_id = ?
            """,
            (user_id, product_id)
        )

        connection.commit()
        connection.close()

    @staticmethod
    def clear(user_id):
        connection = get_connection()

        connection.execute(
            """
            DELETE FROM cart_items
            WHERE user_id = ?
            """,
            (user_id,)
        )

        connection.commit()
        connection.close()


# =========================================================
# ORDERS
# =========================================================

class Order:

    ALLOWED_STATUSES = (
        "pending",
        "confirmed",
        "shipped",
        "in_transit",
        "delivered",
        "cancelled",
        "returned"
    )

    @staticmethod
    def create(
        user_id,
        total_amount,
        delivery_address="",
        delivery_wilaya="",
        delivery_phone=""
    ):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO orders
            (
                user_id,
                total_amount,
                delivery_address,
                delivery_wilaya,
                delivery_phone,
                status
            )
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (
                user_id,
                total_amount,
                delivery_address,
                delivery_wilaya,
                delivery_phone
            )
        )

        connection.commit()
        order_id = cursor.lastrowid
        connection.close()

        return order_id

    @staticmethod
    def find_by_id(order_id):
        connection = get_connection()

        order = connection.execute(
            """
            SELECT *
            FROM orders
            WHERE id = ?
            LIMIT 1
            """,
            (order_id,)
        ).fetchone()

        connection.close()
        return order

    @staticmethod
    def by_user(user_id):
        connection = get_connection()

        orders = connection.execute(
            """
            SELECT *
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()
        return orders

    @staticmethod
    def update_status(order_id, status):
        if status not in Order.ALLOWED_STATUSES:
            return False

        connection = get_connection()

        connection.execute(
            """
            UPDATE orders
            SET status = ?
            WHERE id = ?
            """,
            (status, order_id)
        )

        connection.commit()
        changed = connection.total_changes > 0
        connection.close()

        return changed

    @staticmethod
    def confirm_receipt(order_id, user_id):
        connection = get_connection()

        order = connection.execute(
            """
            SELECT *
            FROM orders
            WHERE id = ?
            AND user_id = ?
            LIMIT 1
            """,
            (order_id, user_id)
        ).fetchone()

        if not order or order["status"] != "delivered":
            connection.close()
            return False

        connection.execute(
            """
            UPDATE orders
            SET status = 'delivered'
            WHERE id = ?
            """,
            (order_id,)
        )

        connection.commit()
        connection.close()

        return True


# =========================================================
# ORDER ITEMS
# =========================================================

class OrderItem:

    @staticmethod
    def create(
        order_id,
        product_id,
        quantity,
        price
    ):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO order_items
            (
                order_id,
                product_id,
                quantity,
                price
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                order_id,
                product_id,
                quantity,
                price
            )
        )

        connection.commit()
        item_id = cursor.lastrowid
        connection.close()

        return item_id

    @staticmethod
    def by_order(order_id):
        connection = get_connection()

        items = connection.execute(
            """
            SELECT
                oi.*,
                p.name,
                p.image
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            """,
            (order_id,)
        ).fetchall()

        connection.close()
        return items


# =========================================================
# REVIEWS
# =========================================================

class Review:

    @staticmethod
    def can_review(user_id, product_id):
        connection = get_connection()

        row = connection.execute(
            """
            SELECT oi.id
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.user_id = ?
            AND oi.product_id = ?
            AND o.status = 'delivered'
            AND NOT EXISTS (
                SELECT 1
                FROM reviews r
                WHERE r.user_id = o.user_id
                AND r.product_id = oi.product_id
            )
            LIMIT 1
            """,
            (user_id, product_id)
        ).fetchone()

        connection.close()

        return row is not None

    @staticmethod
    def create(user_id, product_id, rating, comment=""):
        if not 1 <= int(rating) <= 5:
            return None

        if not Review.can_review(user_id, product_id):
            return None

        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO reviews
                (
                    user_id,
                    product_id,
                    rating,
                    comment
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    product_id,
                    rating,
                    comment
                )
            )

            connection.commit()
            review_id = cursor.lastrowid

        except sqlite3.IntegrityError:
            connection.close()
            return None

        connection.close()

        Product.update_rating(product_id)

        return review_id

    @staticmethod
    def by_product(product_id):
        connection = get_connection()

        reviews = connection.execute(
            """
            SELECT
                r.*,
                u.full_name,
                u.profile_image
            FROM reviews r
            JOIN users u ON u.id = r.user_id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC
            """,
            (product_id,)
        ).fetchall()

        connection.close()
        return reviews


# =========================================================
# STORE FOLLOWERS
# =========================================================

class StoreFollower:

    @staticmethod
    def follow(user_id, store_id):
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO store_followers
                (user_id, store_id)
                VALUES (?, ?)
                """,
                (user_id, store_id)
            )

            connection.execute(
                """
                UPDATE stores
                SET followers_count =
                    COALESCE(followers_count, 0) + 1
                WHERE id = ?
                """,
                (store_id,)
            )

            connection.commit()
            return True

        except sqlite3.IntegrityError:
            return False

        finally:
            connection.close()

    @staticmethod
    def unfollow(user_id, store_id):
        connection = get_connection()

        cursor = connection.execute(
            """
            DELETE FROM store_followers
            WHERE user_id = ?
            AND store_id = ?
            """,
            (user_id, store_id)
        )

        if cursor.rowcount > 0:
            connection.execute(
                """
                UPDATE stores
                SET followers_count =
                    MAX(COALESCE(followers_count, 0) - 1, 0)
                WHERE id = ?
                """,
                (store_id,)
            )

        connection.commit()
        connection.close()

    @staticmethod
    def count(store_id):
        connection = get_connection()

        row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM store_followers
            WHERE store_id = ?
            """,
            (store_id,)
        ).fetchone()

        connection.close()

        return row["total"]


# =========================================================
# MESSAGES
# =========================================================

class Message:

    @staticmethod
    def create(sender_id, receiver_id, body):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO messages
            (
                sender_id,
                receiver_id,
                body
            )
            VALUES (?, ?, ?)
            """,
            (
                sender_id,
                receiver_id,
                body
            )
        )

        connection.commit()
        message_id = cursor.lastrowid
        connection.close()

        return message_id

    @staticmethod
    def conversation(user_id):
        connection = get_connection()

        rows = connection.execute(
            """
            SELECT
                m.*,
                sender.full_name AS sender_name,
                receiver.full_name AS receiver_name
            FROM messages m
            JOIN users sender
                ON sender.id = m.sender_id
            JOIN users receiver
                ON receiver.id = m.receiver_id
            WHERE m.sender_id = ?
               OR m.receiver_id = ?
            ORDER BY m.created_at DESC
            """,
            (user_id, user_id)
        ).fetchall()

        connection.close()
        return rows

    @staticmethod
    def mark_as_read(message_id, user_id):
        connection = get_connection()

        connection.execute(
            """
            UPDATE messages
            SET is_read = 1
            WHERE id = ?
            AND receiver_id = ?
            """,
            (message_id, user_id)
        )

        connection.commit()
        connection.close()


# =========================================================
# NOTIFICATIONS
# =========================================================

class Notification:

    @staticmethod
    def create(
        user_id,
        title,
        body,
        notification_type=""
    ):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                title,
                body,
                type
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                title,
                body,
                notification_type
            )
        )

        connection.commit()
        notification_id = cursor.lastrowid
        connection.close()

        return notification_id

    @staticmethod
    def for_user(user_id):
        connection = get_connection()

        rows = connection.execute(
            """
            SELECT *
            FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()
        return rows

    @staticmethod
    def mark_as_read(notification_id, user_id):
        connection = get_connection()

        connection.execute(
            """
            UPDATE notifications
            SET is_read = 1
            WHERE id = ?
            AND user_id = ?
            """,
            (notification_id, user_id)
        )

        connection.commit()
        connection.close()


# =========================================================
# COMPLAINTS
# =========================================================

class Complaint:

    @staticmethod
    def create(
        user_id,
        subject,
        message,
        order_id=None
    ):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO complaints
            (
                user_id,
                subject,
                message,
                order_id
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                subject,
                message,
                order_id
            )
        )

        connection.commit()
        complaint_id = cursor.lastrowid
        connection.close()

        return complaint_id

    @staticmethod
    def by_user(user_id):
        connection = get_connection()

        rows = connection.execute(
            """
            SELECT *
            FROM complaints
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()
        return rows


# =========================================================
# REPORTS
# =========================================================

class Report:

    @staticmethod
    def create(
        user_id,
        target_type,
        target_id,
        reason,
        details=""
    ):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO reports
            (
                user_id,
                target_type,
                target_id,
                reason,
                details
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                target_type,
                target_id,
                reason,
                details
            )
        )

        connection.commit()
        report_id = cursor.lastrowid
        connection.close()

        return report_id


# =========================================================
# BLOCKED USERS
# =========================================================

class BlockedUser:

    @staticmethod
    def block(user_id, blocked_user_id):
        if user_id == blocked_user_id:
            return False

        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO blocked_users
                (user_id, blocked_user_id)
                VALUES (?, ?)
                """,
                (user_id, blocked_user_id)
            )

            connection.commit()
            return True

        except sqlite3.IntegrityError:
            return False

        finally:
            connection.close()

    @staticmethod
    def unblock(user_id, blocked_user_id):
        connection = get_connection()

        connection.execute(
            """
            DELETE FROM blocked_users
            WHERE user_id = ?
            AND blocked_user_id = ?
            """,
            (user_id, blocked_user_id)
        )

        connection.commit()
        connection.close()

    @staticmethod
    def is_blocked(user_id, other_user_id):
        connection = get_connection()

        row = connection.execute(
            """
            SELECT 1
            FROM blocked_users
            WHERE user_id = ?
            AND blocked_user_id = ?
            LIMIT 1
            """,
            (user_id, other_user_id)
        ).fetchone()

        connection.close()

        return row is not None


# =========================================================
# DISCOUNT CODES
# =========================================================

class DiscountCode:

    @staticmethod
    def create(
        code,
        discount_percent,
        store_id=None,
        expires_at=None,
        usage_limit=None
    ):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO discount_codes
                (
                    code,
                    discount_percent,
                    store_id,
                    expires_at,
                    usage_limit
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    code.upper(),
                    discount_percent,
                    store_id,
                    expires_at,
                    usage_limit
                )
            )

            connection.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            return None

        finally:
            connection.close()


# =========================================================
# PRICE ALERTS
# =========================================================

class PriceAlert:

    @staticmethod
    def create(user_id, product_id, target_price):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO price_alerts
                (
                    user_id,
                    product_id,
                    target_price
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    product_id,
                    target_price
                )
            )

            connection.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            return None

        finally:
            connection.close()


# =========================================================
# PRODUCT VIEWS
# =========================================================

class ProductView:

    @staticmethod
    def add(user_id, product_id):
        connection = get_connection()

        connection.execute(
            """
            INSERT INTO product_views
            (
                user_id,
                product_id
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                product_id
            )
        )

        connection.commit()
        connection.close()

    @staticmethod
    def count(product_id):
        connection = get_connection()

        row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM product_views
            WHERE product_id = ?
            """,
            (product_id,)
        ).fetchone()

        connection.close()

        return row["total"]


# =========================================================
# CHAT SETTINGS
# =========================================================

class ChatSettings:

    @staticmethod
    def get(user_id):
        connection = get_connection()

        row = connection.execute(
            """
            SELECT *
            FROM chat_settings
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

        if row is None:
            connection.execute(
                """
                INSERT INTO chat_settings
                (
                    user_id,
                    voice_type,
                    voice_enabled,
                    language,
                    style
                )
                VALUES (?, 'female', 1, 'ar', 'friendly')
                """,
                (user_id,)
            )

            connection.commit()

            row = connection.execute(
                """
                SELECT *
                FROM chat_settings
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,)
            ).fetchone()

        connection.close()

        return row

    @staticmethod
    def update(
        user_id,
        voice_type=None,
        voice_enabled=None,
        language=None,
        style=None
    ):
        current = ChatSettings.get(user_id)

        new_voice_type = (
            voice_type
            if voice_type in ("female", "male")
            else current["voice_type"]
        )

        new_voice_enabled = (
            int(bool(voice_enabled))
            if voice_enabled is not None
            else current["voice_enabled"]
        )

        new_language = (
            language
            if language in ("ar", "fr", "en")
            else current["language"]
        )

        allowed_styles = (
            "friendly",
            "youthful",
            "funny",
            "professional",
            "darija"
        )

        new_style = (
            style
            if style in allowed_styles
            else current["style"]
        )

        connection = get_connection()

        connection.execute(
            """
            UPDATE chat_settings
            SET
                voice_type = ?,
                voice_enabled = ?,
                language = ?,
                style = ?
            WHERE user_id = ?
            """,
            (
                new_voice_type,
                new_voice_enabled,
                new_language,
                new_style,
                user_id
            )
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM chat_settings
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

        connection.close()

        return row
