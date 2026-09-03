import json
from database import get_connection


# ============================================================
# USER
# ============================================================

class User:

    @staticmethod
    def create(full_name, email, password, role="buyer", phone=""):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO users
                (full_name, email, phone, password, role)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_name, email, phone, password, role)
            )

            connection.commit()
            return cursor.lastrowid

        except Exception:
            connection.rollback()
            return None

        finally:
            connection.close()

    @staticmethod
    def find_by_email(email):
        connection = get_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()
        return user

    @staticmethod
    def find_by_id(user_id):
        connection = get_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        connection.close()
        return user

    @staticmethod
    def update_profile(user_id, full_name=None, phone=None,
                       bio=None, wilaya=None, municipality=None,
                       avatar=None):

        connection = get_connection()

        fields = []
        values = []

        data = {
            "full_name": full_name,
            "phone": phone,
            "bio": bio,
            "wilaya": wilaya,
            "municipality": municipality,
            "avatar": avatar
        }

        for field, value in data.items():
            if value is not None:
                fields.append(f"{field} = ?")
                values.append(value)

        if not fields:
            connection.close()
            return False

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

        return True

    @staticmethod
    def update_settings(user_id, language=None):

        connection = get_connection()

        connection.execute(
            """
            UPDATE users
            SET language = ?
            WHERE id = ?
            """,
            (language, user_id)
        )

        connection.commit()
        connection.close()

        return True

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
    def create(user_id, name, description="",
               phone="", wilaya="", municipality=""):

        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO stores
                (user_id, name, description, phone, wilaya, municipality)
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

        except Exception:
            connection.rollback()
            return None

        finally:
            connection.close()

    @staticmethod
    def find_by_user_id(user_id):

        connection = get_connection()

        store = connection.execute(
            "SELECT * FROM stores WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        connection.close()
        return store

    @staticmethod
    def find_by_id(store_id):

        connection = get_connection()

        store = connection.execute(
            "SELECT * FROM stores WHERE id = ?",
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
            "cover_image"
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
                u.email
            FROM stores s
            JOIN users u ON u.id = s.user_id
            WHERE s.id = ?
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
            SET total_sales = total_sales + 1
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
    def create(store_id, name, price,
               description="", discount=0,
               quantity=0, category=None,
               brand=None, images=None,
               video=None, delivery_wilayas=None):

        connection = get_connection()

        images_json = (
            json.dumps(images, ensure_ascii=False)
            if isinstance(images, list)
            else images
        )

        wilayas_json = (
            json.dumps(delivery_wilayas, ensure_ascii=False)
            if isinstance(delivery_wilayas, list)
            else delivery_wilayas
        )

        cursor = connection.execute(
            """
            INSERT INTO products
            (
                store_id,
                name,
                description,
                price,
                discount,
                quantity,
                category,
                brand,
                images,
                video,
                delivery_wilayas
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                store_id,
                name,
                description,
                price,
                discount,
                quantity,
                category,
                brand,
                images_json,
                video,
                wilayas_json
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
                s.trust_score
            FROM products p
            JOIN stores s ON s.id = p.store_id
            WHERE p.id = ?
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
                COUNT(*) AS reviews_count
            FROM reviews
            WHERE product_id = ?
            """,
            (product_id,)
        ).fetchone()

        rating = result["average_rating"] or 0
        count = result["reviews_count"] or 0

        connection.execute(
            """
            UPDATE products
            SET rating = ?, reviews_count = ?
            WHERE id = ?
            """,
            (rating, count, product_id)
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

        connection.execute(
            """
            INSERT OR IGNORE INTO favorites
            (user_id, product_id)
            VALUES (?, ?)
            """,
            (user_id, product_id)
        )

        connection.commit()
        connection.close()

    @staticmethod
    def remove(user_id, product_id):

        connection = get_connection()

        connection.execute(
            """
            DELETE FROM favorites
            WHERE user_id = ? AND product_id = ?
            """,
            (user_id, product_id)
        )

        connection.commit()
        connection.close()

    @staticmethod
    def all(user_id):

        connection = get_connection()

        products = connection.execute(
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
        return products


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
                p.discount,
                p.images,
                p.quantity AS stock,
                s.name AS store_name
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            JOIN stores s ON s.id = p.store_id
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
            WHERE user_id = ? AND product_id = ?
            """,
            (user_id, product_id)
        )

        connection.commit()
        connection.close()

    @staticmethod
    def clear(user_id):

        connection = get_connection()

        connection.execute(
            "DELETE FROM cart_items WHERE user_id = ?",
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
    def create(user_id, total_amount,
               delivery_address,
               delivery_wilaya,
               delivery_phone):

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
            SET status = 'delivered'
            WHERE id = ?
              AND user_id = ?
              AND status IN ('shipped', 'in_transit')
            """,
            (order_id, user_id)
        )

        connection.commit()
        changed = cursor.rowcount > 0
        connection.close()

        return changed


# ============================================================
# ORDER ITEMS
# ============================================================

class OrderItem:

    @staticmethod
    def create(order_id, product_id,
               quantity, price, store_id=None):

        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO order_items
            (order_id, product_id, store_id, quantity, price)
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
                p.name,
                p.images
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
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
            SELECT o.id
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
            (user_id, product_id)
        ).fetchone()

        connection.close()

        return result is not None

    @staticmethod
    def create(user_id, product_id,
               order_id, rating,
               comment="", order_item_id=None):

        if not 1 <= int(rating) <= 5:
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

        except Exception:

            connection.rollback()
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

        connection.execute(
            """
            INSERT OR IGNORE INTO store_followers
            (user_id, store_id)
            VALUES (?, ?)
            """,
            (user_id, store_id)
        )

        connection.commit()
        connection.close()

    @staticmethod
    def unfollow(user_id, store_id):

        connection = get_connection()

        connection.execute(
            """
            DELETE FROM store_followers
            WHERE user_id = ? AND store_id = ?
            """,
            (user_id, store_id)
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
            (sender_id, receiver_id, body)
            VALUES (?, ?, ?)
            """,
            (sender_id, receiver_id, body)
        )

        connection.commit()
        message_id = cursor.lastrowid
        connection.close()

        return message_id

    @staticmethod
    def conversation(user_id):

        connection = get_connection()

        messages = connection.execute(
            """
            SELECT
                m.*,
                CASE
                    WHEN m.sender_id = ?
                    THEN receiver.full_name
                    ELSE sender.full_name
                END AS other_name
            FROM messages m
            JOIN users sender
                ON sender.id = m.sender_id
            JOIN users receiver
                ON receiver.id = m.receiver_id
            WHERE m.sender_id = ?
               OR m.receiver_id = ?
            ORDER BY m.created_at DESC
            """,
            (user_id, user_id, user_id)
        ).fetchall()

        connection.close()
        return messages

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
            (user_id, sender_id)
        )

        connection.commit()
        connection.close()


# ============================================================
# NOTIFICATIONS
# ============================================================

class Notification:

    @staticmethod
    def create(user_id, title, message):

        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO notifications
            (user_id, title, message)
            VALUES (?, ?, ?)
            """,
            (user_id, title, message)
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
            WHERE id = ? AND user_id = ?
            """,
            (notification_id, user_id)
        )

        connection.commit()
        connection.close()


# ============================================================
# COMPLAINTS
# ============================================================

class Complaint:

    @staticmethod
    def create(user_id, message,
               order_id=None, subject=""):

        connection = get_connection()

        cursor = connection.execute(
            """
            INSERT INTO complaints
            (user_id, order_id, subject, message)
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
    def create(user_id, target_type,
               target_id, reason, message=""):

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
            (blocker_id, blocked_id)
            VALUES (?, ?)
            """,
            (blocker_id, blocked_id)
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
            (blocker_id, blocked_id)
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
            """,
            (blocker_id, blocked_id)
        ).fetchone()

        connection.close()

        return result is not None


# ============================================================
# DISCOUNT CODES
# ============================================================

class DiscountCode:

    @staticmethod
    def create(store_id, code,
               discount_percent,
               usage_limit=0,
               expires_at=None):

        connection = get_connection()

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
                code.upper(),
                discount_percent,
                usage_limit,
                expires_at
            )
        )

        connection.commit()
        code_id = cursor.lastrowid
        connection.close()

        return code_id

    @staticmethod
    def find(code):

        connection = get_connection()

        result = connection.execute(
            """
            SELECT *
            FROM discount_codes
            WHERE code = ?
              AND active = 1
            """,
            (code.upper(),)
        ).fetchone()

        connection.close()
        return result

    @staticmethod
    def use(code):

        connection = get_connection()

        result = connection.execute(
            """
            SELECT *
            FROM discount_codes
            WHERE code = ?
              AND active = 1
            """,
            (code.upper(),)
        ).fetchone()

        if not result:
            connection.close()
            return False

        if (
            result["max_uses"] > 0
            and result["used_count"] >= result["max_uses"]
        ):
            connection.close()
            return False

        connection.execute(
            """
            UPDATE discount_codes
            SET used_count = used_count + 1
            WHERE id = ?
            """,
            (result["id"],)
        )

        connection.commit()
        connection.close()

        return True


# ============================================================
# PRICE ALERTS
# ============================================================

class PriceAlert:

    @staticmethod
    def create(user_id, product_id, target_price):

        connection = get_connection()

        connection.execute(
            """
            INSERT INTO price_alerts
            (user_id, product_id, target_price)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id)
            DO UPDATE SET
                target_price = excluded.target_price,
                active = 1
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
            (user_id, product_id)
            VALUES (?, ?)
            """,
            (user_id, product_id)
        )

        connection.execute(
            """
            UPDATE products
            SET views = views + 1
            WHERE id = ?
            """,
            (product_id,)
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
            """,
            (user_id,)
        ).fetchone()

        if not settings:

            connection.execute(
                """
                INSERT INTO chat_settings
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
                """,
                (user_id,)
            ).fetchone()

        connection.close()

        return settings

    @staticmethod
    def update(user_id,
               voice_type="female",
               voice_enabled=False,
               language="ar",
               style="friendly"):

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

        return True
