import sqlite3
from database import get_connection


# ============================================================
# DZ MARKET 🇩🇿
# MODELS
# ============================================================


class User:

    @staticmethod
    def create(full_name, email, password, role="buyer", phone=""):
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
                    phone
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    full_name,
                    email,
                    password,
                    role,
                    phone
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
            WHERE email = ?
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
    def update_profile(user_id, full_name=None, phone=None, profile_image=None):
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
            values.append(dark_mode)

        if notifications_enabled is not None:
            fields.append("notifications_enabled = ?")
            values.append(notifications_enabled)

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


# ============================================================
# STORE
# ============================================================

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
    def update(store_id, **fields):
        allowed = {
            "name",
            "description",
            "phone",
            "wilaya",
            "municipality",
            "logo",
            "cover_image",
            "opening_hours"
        }

        updates = []
        values = []

        for key, value in fields.items():
            if key in allowed:
                updates.append(f"{key} = ?")
                values.append(value)

        if not updates:
            return False

        values.append(store_id)

        connection = get_connection()

        connection.execute(
            f"""
            UPDATE stores
            SET {", ".join(updates)}
            WHERE id = ?
            """,
            values
        )

        connection.commit()
        connection.close()

        return True


    @staticmethod
    def public_profile(store_id):
        connection = get_connection()

        store = connection.execute(
            """
            SELECT
                s.*,
                u.full_name,
                u.seller_verification_status,
                u.seller_activity_type
            FROM stores s
            JOIN users u
                ON u.id = s.user_id
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
            SET sales_count = sales_count + 1
            WHERE id = ?
            """,
            (store_id,)
        )

        connection.commit()
        connection.close()


    @staticmethod
    def update_trust_score(store_id, score):
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


# ============================================================
# PRODUCT
# ============================================================

class Product:

    @staticmethod
    def create(
        store_id,
        name,
        description="",
        brand_name="",
        brand_logo="",
        price=0,
        old_price=0,
        discount_percent=0,
        quantity=0,
        category="",
        image="",
        video="",
        is_algerian=0,
        delivery_wilayas=""
    ):
        connection = get_connection()

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
                is_algerian,
                delivery_wilayas
            )
        )

        connection.commit()
        product_id = cursor.lastrowid
        connection.close()

        return product_id


    @staticmethod
    def find_by_id(product_id):
        connection = get_connection()

        product = connection.execute(
            """
            SELECT
                p.*,
                s.name AS store_name,
                s.trust_score,
                u.seller_verification_status
            FROM products p
            JOIN stores s
                ON s.id = p.store_id
            JOIN users u
                ON u.id = s.user_id
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

        rating = result["average_rating"] or 0
        reviews_count = result["review_count"] or 0

        connection.execute(
            """
            UPDATE products
            SET
                rating = ?,
                reviews_count = ?
            WHERE id = ?
            """,
            (
                rating,
                reviews_count,
                product_id
            )
        )

        connection.commit()
        connection.close()


# ============================================================
# FAVORITES
# ============================================================

class Favorite:

    @staticmethod
    def add(user_id, product_id):
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT OR IGNORE INTO favorites
                (user_id, product_id)
                VALUES (?, ?)
                """,
                (user_id, product_id)
            )

            connection.commit()
            return True

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

        items = connection.execute(
            """
            SELECT
                p.*,
                f.created_at AS favorited_at
            FROM favorites f
            JOIN products p
                ON p.id = f.product_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()
        return items


# ============================================================
# CART
# ============================================================

class Cart:

    @staticmethod
    def add(user_id, product_id, quantity=1):
        connection = get_connection()

        connection.execute(
            """
            INSERT INTO cart_items
            (
                user_id,
                product_id,
                quantity
            )
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id)
            DO UPDATE SET
                quantity = quantity + excluded.quantity
            """,
            (
                user_id,
                product_id,
                quantity
            )
        )

        connection.commit()
        connection.close()


    @staticmethod
    def get_items(user_id):
        connection = get_connection()

        items = connection.execute(
            """
            SELECT
                c.id AS cart_id,
                c.quantity AS cart_quantity,
                p.*,
                s.name AS store_name
            FROM cart_items c
            JOIN products p
                ON p.id = c.product_id
            JOIN stores s
                ON s.id = p.store_id
            WHERE c.user_id = ?
            AND p.is_active = 1
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


# ============================================================
# ORDERS
# ============================================================

class Order:

    ALLOWED_STATUSES = {
        "pending",
        "confirmed",
        "shipped",
        "in_transit",
        "delivered",
        "cancelled",
        "returned"
    }


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
                delivery_phone
            )
            VALUES (?, ?, ?, ?, ?)
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
        connection.close()

        return True


    @staticmethod
    def confirm_receipt(order_id, user_id):
        connection = get_connection()

        cursor = connection.execute(
            """
            UPDATE orders
            SET
                buyer_confirmed = 1,
                status = 'delivered'
            WHERE id = ?
            AND user_id = ?
            """,
            (
                order_id,
                user_id
            )
        )

        connection.commit()
        success = cursor.rowcount > 0
        connection.close()

        return success


# ============================================================
# ORDER ITEMS
# ============================================================

class OrderItem:

    @staticmethod
    def create(
        order_id,
        product_id,
        quantity,
        price,
        store_id=None
    ):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO order_items
            (
                order_id,
                product_id,
                store_id,
                quantity,
                price
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                order_id,
                product_id,
                store_id,
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
                p.name AS product_name,
                p.image AS product_image
            FROM order_items oi
            JOIN products p
                ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY oi.id ASC
            """,
            (order_id,)
        ).fetchall()

        connection.close()
        return items


# ============================================================
# REVIEWS
# ============================================================

class Review:

    @staticmethod
    def can_review(user_id, product_id):
        connection = get_connection()

        result = connection.execute(
            """
            SELECT oi.id
            FROM orders o
            JOIN order_items oi
                ON oi.order_id = o.id
            LEFT JOIN reviews r
                ON r.order_id = o.id
                AND r.product_id = oi.product_id
                AND r.user_id = o.user_id
            WHERE o.user_id = ?
            AND oi.product_id = ?
            AND o.status = 'delivered'
            AND r.id IS NULL
            LIMIT 1
            """,
            (
                user_id,
                product_id
            )
        ).fetchone()

        connection.close()

        return result is not None


    @staticmethod
    def create(
        user_id,
        product_id,
        order_id,
        rating,
        comment="",
        order_item_id=None
    ):
        if rating < 1 or rating > 5:
            return None

        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO reviews
                (
                    user_id,
                    product_id,
                    order_id,
                    order_item_id,
                    rating,
                    comment
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    product_id,
                    order_id,
                    order_item_id,
                    rating,
                    comment
                )
            )

            connection.commit()
            review_id = cursor.lastrowid

        except sqlite3.IntegrityError:
            review_id = None

        finally:
            connection.close()

        if review_id:
            Product.update_rating(product_id)

        return review_id


# ============================================================
# STORE FOLLOWERS
# ============================================================

class StoreFollower:

    @staticmethod
    def follow(user_id, store_id):
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT OR IGNORE INTO store_followers
                (user_id, store_id)
                VALUES (?, ?)
                """,
                (
                    user_id,
                    store_id
                )
            )

            connection.execute(
                """
                UPDATE stores
                SET followers_count = (
                    SELECT COUNT(*)
                    FROM store_followers
                    WHERE store_id = ?
                )
                WHERE id = ?
                """,
                (
                    store_id,
                    store_id
                )
            )

            connection.commit()

        finally:
            connection.close()


    @staticmethod
    def unfollow(user_id, store_id):
        connection = get_connection()

        connection.execute(
            """
            DELETE FROM store_followers
            WHERE user_id = ?
            AND store_id = ?
            """,
            (
                user_id,
                store_id
            )
        )

        connection.execute(
            """
            UPDATE stores
            SET followers_count = (
                SELECT COUNT(*)
                FROM store_followers
                WHERE store_id = ?
            )
            WHERE id = ?
            """,
            (
                store_id,
                store_id
            )
        )

        connection.commit()
        connection.close()


    @staticmethod
    def count(store_id):
        connection = get_connection()

        result = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM store_followers
            WHERE store_id = ?
            """,
            (store_id,)
        ).fetchone()

        connection.close()

        return result["count"]


# ============================================================
# MESSAGES
# ============================================================

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

        conversations = connection.execute(
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
            (
                user_id,
                user_id
            )
        ).fetchall()

        connection.close()

        return conversations


    @staticmethod
    def mark_as_read(user_id, sender_id):
        connection = get_connection()

        connection.execute(
            """
            UPDATE messages
            SET is_read = 1
            WHERE receiver_id = ?
            AND sender_id = ?
            """,
            (
                user_id,
                sender_id
            )
        )

        connection.commit()
        connection.close()


# ============================================================
# NOTIFICATIONS
# ============================================================

class Notification:

    @staticmethod
    def create(
        user_id,
        title,
        message
    ):
        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                title,
                message
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                title,
                message
            )
        )

        connection.commit()
        notification_id = cursor.lastrowid
        connection.close()

        return notification_id


    @staticmethod
    def by_user(user_id):
        connection = get_connection()

        notifications = connection.execute(
            """
            SELECT *
            FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()

        return notifications


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
            (
                notification_id,
                user_id
            )
        )

        connection.commit()
        connection.close()


# ============================================================
# COMPLAINTS
# ============================================================

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
                order_id,
                subject,
                message
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                order_id,
                subject,
                message
            )
        )

        connection.commit()
        complaint_id = cursor.lastrowid
        connection.close()

        return complaint_id


    @staticmethod
    def by_user(user_id):
        connection = get_connection()

        complaints = connection.execute(
            """
            SELECT *
            FROM complaints
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()

        return complaints


# ============================================================
# REPORTS
# ============================================================

class Report:

    @staticmethod
    def create(
        user_id,
        target_type,
        target_id,
        reason,
        message=""
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
                message
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                target_type,
                target_id,
                reason,
                message
            )
        )

        connection.commit()
        report_id = cursor.lastrowid
        connection.close()

        return report_id


# ============================================================
# BLOCKED USERS
# ============================================================

class BlockedUser:

    @staticmethod
    def block(blocker_id, blocked_id):
        if blocker_id == blocked_id:
            return False

        connection = get_connection()

        connection.execute(
            """
            INSERT OR IGNORE INTO blocked_users
            (
                blocker_id,
                blocked_id
            )
            VALUES (?, ?)
            """,
            (
                blocker_id,
                blocked_id
            )
        )

        connection.commit()
        connection.close()

        return True


    @staticmethod
    def unblock(blocker_id, blocked_id):
        connection = get_connection()

        connection.execute(
            """
            DELETE FROM blocked_users
            WHERE blocker_id = ?
            AND blocked_id = ?
            """,
            (
                blocker_id,
                blocked_id
            )
        )

        connection.commit()
        connection.close()


    @staticmethod
    def is_blocked(blocker_id, blocked_id):
        connection = get_connection()

        result = connection.execute(
            """
            SELECT id
            FROM blocked_users
            WHERE blocker_id = ?
            AND blocked_id = ?
            LIMIT 1
            """,
            (
                blocker_id,
                blocked_id
            )
        ).fetchone()

        connection.close()

        return result is not None


# ============================================================
# DISCOUNT CODES
# ============================================================

class DiscountCode:

    @staticmethod
    def create(
        code,
        discount_percent,
        store_id=None,
        expires_at=None,
        usage_limit=0
    ):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO discount_codes
                (
                    store_id,
                    code,
                    discount_percent,
                    max_uses,
                    expires_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    store_id,
                    code,
                    discount_percent,
                    usage_limit,
                    expires_at
                )
            )

            connection.commit()
            discount_id = cursor.lastrowid

        except sqlite3.IntegrityError:
            discount_id = None

        finally:
            connection.close()

        return discount_id


    @staticmethod
    def find(code):
        connection = get_connection()

        discount = connection.execute(
            """
            SELECT *
            FROM discount_codes
            WHERE code = ?
            AND is_active = 1
            LIMIT 1
            """,
            (code,)
        ).fetchone()

        connection.close()

        return discount


    @staticmethod
    def use(code):
        connection = get_connection()

        connection.execute(
            """
            UPDATE discount_codes
            SET used_count = used_count + 1
            WHERE code = ?
            AND is_active = 1
            AND (
                max_uses = 0
                OR used_count < max_uses
            )
            """,
            (code,)
        )

        connection.commit()
        connection.close()


# ============================================================
# PRICE ALERTS
# ============================================================

class PriceAlert:

    @staticmethod
    def create(
        user_id,
        product_id,
        target_price
    ):
        connection = get_connection()

        connection.execute(
            """
            INSERT INTO price_alerts
            (
                user_id,
                product_id,
                target_price
            )
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id)
            DO UPDATE SET
                target_price = excluded.target_price,
                is_active = 1
            """,
            (
                user_id,
                product_id,
                target_price
            )
        )

        connection.commit()
        connection.close()


# ============================================================
# PRODUCT VIEWS
# ============================================================

class ProductView:

    @staticmethod
    def add(product_id, user_id=None):
        connection = get_connection()

        connection.execute(
            """
            INSERT INTO product_views
            (
                product_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                product_id,
                user_id
            )
        )

        connection.commit()
        connection.close()


    @staticmethod
    def count(product_id):
        connection = get_connection()

        result = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM product_views
            WHERE product_id = ?
            """,
            (product_id,)
        ).fetchone()

        connection.close()

        return result["count"]


# ============================================================
# CHAT SETTINGS
# ============================================================

class ChatSettings:

    @staticmethod
    def get(user_id):
        connection = get_connection()

        settings = connection.execute(
            """
            SELECT *
            FROM chat_settings
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

        if not settings:
            connection.execute(
                """
                INSERT OR IGNORE INTO chat_settings
                (user_id)
                VALUES (?)
                """,
                (user_id,)
            )

            connection.commit()

            settings = connection.execute(
                """
                SELECT *
                FROM chat_settings
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,)
            ).fetchone()

        connection.close()

        return settings


    @staticmethod
    def update(
        user_id,
        voice_type="female",
        voice_enabled=True,
        language="ar",
        style="friendly"
    ):
        allowed_languages = {
            "ar",
            "tz",
            "dz",
            "fr",
            "en"
        }

        allowed_styles = {
            "friendly",
            "youthful",
            "funny",
            "professional",
            "darija"
        }

        if language not in allowed_languages:
            language = "ar"

        if style not in allowed_styles:
            style = "friendly"

        if voice_type not in {
            "female",
            "male"
        }:
            voice_type = "female"

        connection = get_connection()

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
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(user_id)
            DO UPDATE SET
                voice_type = excluded.voice_type,
                voice_enabled = excluded.voice_enabled,
                language = excluded.language,
                style = excluded.style
            """,
            (
                user_id,
                voice_type,
                1 if voice_enabled else 0,
                language,
                style
            )
        )

        connection.commit()
        connection.close()
