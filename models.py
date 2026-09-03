import sqlite3
import secrets
import string
from datetime import datetime
from database import get_db


def generate_code(prefix="DZ"):
    chars = string.ascii_uppercase + string.digits
    return prefix + "-" + "".join(secrets.choice(chars) for _ in range(8))


class User:

    @staticmethod
    def create(full_name, email, phone, password, role="buyer", referral_code=None):
        db = get_db()

        code = referral_code or generate_code("DZ")

        cur = db.execute("""
            INSERT INTO users
            (full_name, email, phone, password, role, referral_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            full_name,
            email,
            phone,
            password,
            role,
            code
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def find_by_email(email):
        db = get_db()
        return db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

    @staticmethod
    def find_by_id(user_id):
        db = get_db()
        return db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

    @staticmethod
    def find_by_referral_code(code):
        db = get_db()
        return db.execute(
            "SELECT * FROM users WHERE referral_code = ?",
            (code,)
        ).fetchone()

    @staticmethod
    def update_profile(user_id, **data):
        allowed = [
            "full_name",
            "phone",
            "avatar",
            "bio",
            "wilaya",
            "municipality"
        ]

        fields = []
        values = []

        for key in allowed:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])

        if not fields:
            return

        values.append(user_id)

        db = get_db()
        db.execute(
            f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()

    @staticmethod
    def update_settings(user_id, **data):
        allowed = ["language"]

        fields = []
        values = []

        for key in allowed:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])

        if not fields:
            return

        values.append(user_id)

        db = get_db()
        db.execute(
            f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()

    @staticmethod
    def verify_phone(user_id):
        db = get_db()
        db.execute(
            "UPDATE users SET phone_verified = 1 WHERE id = ?",
            (user_id,)
        )
        db.commit()


class Store:

    @staticmethod
    def create(user_id, name, description="", phone=None,
               wilaya=None, municipality=None):
        db = get_db()

        cur = db.execute("""
            INSERT INTO stores
            (user_id, name, description, phone, wilaya, municipality)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            name,
            description,
            phone,
            wilaya,
            municipality
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def find_by_user_id(user_id):
        db = get_db()
        return db.execute(
            "SELECT * FROM stores WHERE user_id = ?",
            (user_id,)
        ).fetchone()

    @staticmethod
    def find_by_id(store_id):
        db = get_db()
        return db.execute(
            "SELECT * FROM stores WHERE id = ?",
            (store_id,)
        ).fetchone()

    @staticmethod
    def update(store_id, **data):
        allowed = [
            "name",
            "description",
            "phone",
            "wilaya",
            "municipality",
            "logo",
            "cover_image"
        ]

        fields = []
        values = []

        for key in allowed:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])

        if not fields:
            return

        values.append(store_id)

        db = get_db()
        db.execute(
            f"UPDATE stores SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()

    @staticmethod
    def public_profile(store_id):
        db = get_db()
        return db.execute("""
            SELECT
                s.*,
                u.full_name
            FROM stores s
            JOIN users u ON u.id = s.user_id
            WHERE s.id = ?
        """, (store_id,)).fetchone()

    @staticmethod
    def increment_sales(store_id):
        db = get_db()
        db.execute("""
            UPDATE stores
            SET total_sales = total_sales + 1
            WHERE id = ?
        """, (store_id,))
        db.commit()

    @staticmethod
    def update_trust_score(store_id, score):
        db = get_db()
        db.execute("""
            UPDATE stores
            SET trust_score = ?
            WHERE id = ?
        """, (score, store_id))
        db.commit()


class Product:

    @staticmethod
    def create(store_id, name, description="", price=0,
               discount=0, quantity=0, category=None,
               brand=None, images=None, video=None,
               delivery_wilayas=None):

        db = get_db()

        cur = db.execute("""
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
        """, (
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
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def find_by_id(product_id):
        db = get_db()
        return db.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

    @staticmethod
    def by_store(store_id):
        db = get_db()
        return db.execute("""
            SELECT *
            FROM products
            WHERE store_id = ?
            ORDER BY created_at DESC
        """, (store_id,)).fetchall()

    @staticmethod
    def update(product_id, **data):
        allowed = [
            "name",
            "description",
            "price",
            "discount",
            "quantity",
            "category",
            "brand",
            "images",
            "video",
            "delivery_wilayas",
            "active"
        ]

        fields = []
        values = []

        for key in allowed:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])

        if not fields:
            return

        values.append(product_id)

        db = get_db()
        db.execute(
            f"UPDATE products SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()

    @staticmethod
    def update_rating(product_id, rating):
        db = get_db()

        row = db.execute("""
            SELECT rating, reviews_count
            FROM products
            WHERE id = ?
        """, (product_id,)).fetchone()

        if not row:
            return

        old_rating = float(row["rating"] or 0)
        count = int(row["reviews_count"] or 0)

        new_count = count + 1
        new_rating = (
            (old_rating * count) + float(rating)
        ) / new_count

        db.execute("""
            UPDATE products
            SET rating = ?, reviews_count = ?
            WHERE id = ?
        """, (
            round(new_rating, 2),
            new_count,
            product_id
        ))

        db.commit()


class Favorite:

    @staticmethod
    def add(user_id, product_id):
        db = get_db()

        db.execute("""
            INSERT OR IGNORE INTO favorites
            (user_id, product_id)
            VALUES (?, ?)
        """, (user_id, product_id))

        db.commit()

    @staticmethod
    def remove(user_id, product_id):
        db = get_db()

        db.execute("""
            DELETE FROM favorites
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id))

        db.commit()

    @staticmethod
    def all(user_id):
        db = get_db()

        return db.execute("""
            SELECT
                f.*,
                p.name,
                p.price,
                p.discount,
                p.images
            FROM favorites f
            JOIN products p ON p.id = f.product_id
            WHERE f.user_id = ?
            ORDER BY f.id DESC
        """, (user_id,)).fetchall()


class Cart:

    @staticmethod
    def add(user_id, product_id, quantity=1):
        db = get_db()

        existing = db.execute("""
            SELECT *
            FROM cart_items
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id)).fetchone()

        if existing:
            db.execute("""
                UPDATE cart_items
                SET quantity = quantity + ?
                WHERE user_id = ? AND product_id = ?
            """, (
                quantity,
                user_id,
                product_id
            ))
        else:
            db.execute("""
                INSERT INTO cart_items
                (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            """, (
                user_id,
                product_id,
                quantity
            ))

        db.commit()

    @staticmethod
    def get_items(user_id):
        db = get_db()

        return db.execute("""
            SELECT
                c.*,
                p.name,
                p.price,
                p.discount,
                p.images,
                p.quantity AS stock_quantity,
                p.store_id
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = ?
            ORDER BY c.id DESC
        """, (user_id,)).fetchall()

    @staticmethod
    def update_quantity(user_id, product_id, quantity):
        db = get_db()

        db.execute("""
            UPDATE cart_items
            SET quantity = ?
            WHERE user_id = ? AND product_id = ?
        """, (
            quantity,
            user_id,
            product_id
        ))

        db.commit()

    @staticmethod
    def remove(user_id, product_id):
        db = get_db()

        db.execute("""
            DELETE FROM cart_items
            WHERE user_id = ? AND product_id = ?
        """, (
            user_id,
            product_id
        ))

        db.commit()

    @staticmethod
    def clear(user_id):
        db = get_db()

        db.execute(
            "DELETE FROM cart_items WHERE user_id = ?",
            (user_id,)
        )

        db.commit()


class Order:

    ALLOWED_STATUSES = [
        "pending",
        "confirmed",
        "shipped",
        "in_transit",
        "delivered",
        "cancelled",
        "returned"
    ]

    @staticmethod
    def create(user_id, total_amount,
               delivery_wilaya=None,
               delivery_municipality=None,
               status="pending"):

        db = get_db()

        cur = db.execute("""
            INSERT INTO orders
            (
                user_id,
                total_amount,
                delivery_wilaya,
                delivery_municipality,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            total_amount,
            delivery_wilaya,
            delivery_municipality,
            status
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def find_by_id(order_id):
        db = get_db()

        return db.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

    @staticmethod
    def by_user(user_id):
        db = get_db()

        return db.execute("""
            SELECT *
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()

    @staticmethod
    def update_status(order_id, status):

        if status not in Order.ALLOWED_STATUSES:
            return False

        db = get_db()

        db.execute("""
            UPDATE orders
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            status,
            order_id
        ))

        db.commit()
        return True

    @staticmethod
    def confirm_receipt(order_id, user_id):

        db = get_db()

        result = db.execute("""
            UPDATE orders
            SET status = 'delivered',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            AND user_id = ?
        """, (
            order_id,
            user_id
        ))

        db.commit()

        return result.rowcount > 0


class OrderItem:

    @staticmethod
    def create(order_id, product_id, store_id,
               quantity, price):

        db = get_db()

        cur = db.execute("""
            INSERT INTO order_items
            (
                order_id,
                product_id,
                store_id,
                quantity,
                price
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            order_id,
            product_id,
            store_id,
            quantity,
            price
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def by_order(order_id):

        db = get_db()

        return db.execute("""
            SELECT
                oi.*,
                p.name,
                p.images
            FROM order_items oi
            LEFT JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        """, (order_id,)).fetchall()


class Review:

    @staticmethod
    def can_review(user_id, product_id):

        db = get_db()

        row = db.execute("""
            SELECT oi.id
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.user_id = ?
            AND oi.product_id = ?
            AND o.status = 'delivered'
            LIMIT 1
        """, (
            user_id,
            product_id
        )).fetchone()

        return bool(row)

    @staticmethod
    def create(user_id, product_id, rating, comment=""):

        db = get_db()

        cur = db.execute("""
            INSERT INTO reviews
            (
                user_id,
                product_id,
                rating,
                comment
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            product_id,
            rating,
            comment
        ))

        db.commit()
        return cur.lastrowid


class StoreFollower:

    @staticmethod
    def follow(user_id, store_id):

        db = get_db()

        db.execute("""
            INSERT OR IGNORE INTO store_followers
            (user_id, store_id)
            VALUES (?, ?)
        """, (
            user_id,
            store_id
        ))

        db.commit()

    @staticmethod
    def unfollow(user_id, store_id):

        db = get_db()

        db.execute("""
            DELETE FROM store_followers
            WHERE user_id = ? AND store_id = ?
        """, (
            user_id,
            store_id
        ))

        db.commit()

    @staticmethod
    def count(store_id):

        db = get_db()

        row = db.execute("""
            SELECT COUNT(*) AS total
            FROM store_followers
            WHERE store_id = ?
        """, (store_id,)).fetchone()

        return row["total"] if row else 0


class Message:

    @staticmethod
    def create(sender_id, receiver_id, body):

        db = get_db()

        cur = db.execute("""
            INSERT INTO messages
            (
                sender_id,
                receiver_id,
                body
            )
            VALUES (?, ?, ?)
        """, (
            sender_id,
            receiver_id,
            body
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def between(user1_id, user2_id):

        db = get_db()

        return db.execute("""
            SELECT *
            FROM messages
            WHERE
                (sender_id = ? AND receiver_id = ?)
                OR
                (sender_id = ? AND receiver_id = ?)
            ORDER BY created_at ASC, id ASC
        """, (
            user1_id,
            user2_id,
            user2_id,
            user1_id
        )).fetchall()

    @staticmethod
    def conversation(user_id):

        db = get_db()

        return db.execute("""
            SELECT
                m.*,
                CASE
                    WHEN m.sender_id = ?
                    THEN receiver.full_name
                    ELSE sender.full_name
                END AS other_name,

                CASE
                    WHEN m.sender_id = ?
                    THEN receiver.id
                    ELSE sender.id
                END AS other_id

            FROM messages m

            JOIN users sender
                ON sender.id = m.sender_id

            JOIN users receiver
                ON receiver.id = m.receiver_id

            WHERE m.id IN (

                SELECT MAX(m2.id)
                FROM messages m2
                WHERE
                    m2.sender_id = ?
                    OR
                    m2.receiver_id = ?

                GROUP BY
                    CASE
                        WHEN m2.sender_id = ?
                        THEN m2.receiver_id
                        ELSE m2.sender_id
                    END
            )

            ORDER BY m.created_at DESC
        """, (
            user_id,
            user_id,
            user_id,
            user_id,
            user_id
        )).fetchall()

    @staticmethod
    def mark_as_read(user_id, other_user_id):

        db = get_db()

        try:
            db.execute("""
                UPDATE messages
                SET is_read = 1
                WHERE receiver_id = ?
                AND sender_id = ?
            """, (
                user_id,
                other_user_id
            ))

            db.commit()

        except sqlite3.OperationalError:
            pass


class Notification:

    @staticmethod
    def create(user_id, title, body):

        db = get_db()

        cur = db.execute("""
            INSERT INTO notifications
            (
                user_id,
                title,
                body
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            title,
            body
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def by_user(user_id):

        db = get_db()

        return db.execute("""
            SELECT *
            FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()

    @staticmethod
    def mark_as_read(notification_id, user_id):

        db = get_db()

        db.execute("""
            UPDATE notifications
            SET is_read = 1
            WHERE id = ? AND user_id = ?
        """, (
            notification_id,
            user_id
        ))

        db.commit()


class Complaint:

    @staticmethod
    def create(user_id, subject, body):

        db = get_db()

        cur = db.execute("""
            INSERT INTO complaints
            (
                user_id,
                subject,
                body
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            subject,
            body
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def by_user(user_id):

        db = get_db()

        return db.execute("""
            SELECT *
            FROM complaints
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()


class RewardCard:

    @staticmethod
    def create(user_id, title, description="",
               discount_percent=0,
               reward_type="discount",
               source="system",
               expires_at=None):

        db = get_db()

        code = generate_code("CARD")

        cur = db.execute("""
            INSERT INTO reward_cards
            (
                user_id,
                code,
                title,
                description,
                discount_percent,
                reward_type,
                source,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            code,
            title,
            description,
            discount_percent,
            reward_type,
            source,
            expires_at
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def by_user(user_id):

        db = get_db()

        return db.execute("""
            SELECT *
            FROM reward_cards
            WHERE user_id = ?
            AND active = 1
            AND used = 0
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()

    @staticmethod
    def find_by_code(user_id, code):

        db = get_db()

        return db.execute("""
            SELECT *
            FROM reward_cards
            WHERE user_id = ?
            AND code = ?
            AND active = 1
            AND used = 0
            LIMIT 1
        """, (
            user_id,
            code
        )).fetchone()

    @staticmethod
    def use(card_id):

        db = get_db()

        db.execute("""
            UPDATE reward_cards
            SET used = 1
            WHERE id = ?
        """, (card_id,))

        db.commit()


class Referral:

    @staticmethod
    def create(inviter_id, invited_user_id, referral_code):

        db = get_db()

        cur = db.execute("""
            INSERT OR IGNORE INTO referrals
            (
                inviter_id,
                invited_user_id,
                referral_code
            )
            VALUES (?, ?, ?)
        """, (
            inviter_id,
            invited_user_id,
            referral_code
        ))

        db.commit()
        return cur.lastrowid

    @staticmethod
    def by_inviter(inviter_id):

        db = get_db()

        return db.execute("""
            SELECT *
            FROM referrals
            WHERE inviter_id = ?
            ORDER BY created_at DESC
        """, (inviter_id,)).fetchall()

    @staticmethod
    def complete(invited_user_id):

        db = get_db()

        row = db.execute("""
            SELECT *
            FROM referrals
            WHERE invited_user_id = ?
            AND status != 'completed'
            LIMIT 1
        """, (invited_user_id,)).fetchone()

        if not row:
            return None

        db.execute("""
            UPDATE referrals
            SET status = 'completed',
                reward_granted = 1,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (row["id"],))

        db.commit()

        return row


class RewardMilestone:

    @staticmethod
    def completed_orders(user_id):

        db = get_db()

        row = db.execute("""
            SELECT COUNT(*) AS total
            FROM orders
            WHERE user_id = ?
            AND status = 'delivered'
        """, (user_id,)).fetchone()

        return int(row["total"] or 0)

    @staticmethod
    def has_achieved(user_id, milestone):

        db = get_db()

        row = db.execute("""
            SELECT id
            FROM reward_milestones
            WHERE user_id = ?
            AND milestone = ?
            LIMIT 1
        """, (
            user_id,
            milestone
        )).fetchone()

        return bool(row)

    @staticmethod
    def grant_milestone(user_id, milestone, reward_card_id):

        db = get_db()

        db.execute("""
            INSERT OR IGNORE INTO reward_milestones
            (
                user_id,
                milestone,
                reward_card_id
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            milestone,
            reward_card_id
        ))

        db.commit()


class PriceAlert:

    @staticmethod
    def create(user_id, product_id, target_price):

        db = get_db()

        cur = db.execute("""
            INSERT INTO price_alerts
            (
                user_id,
                product_id,
                target_price
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            product_id,
            target_price
        ))

        db.commit()
        return cur.lastrowid


class ProductView:

    @staticmethod
    def add(user_id, product_id):

        db = get_db()

        db.execute("""
            INSERT INTO product_views
            (
                user_id,
                product_id
            )
            VALUES (?, ?)
        """, (
            user_id,
            product_id
        ))

        db.execute("""
            UPDATE products
            SET views = views + 1
            WHERE id = ?
        """, (product_id,))

        db.commit()

    @staticmethod
    def count(product_id):

        db = get_db()

        row = db.execute("""
            SELECT COUNT(*) AS total
            FROM product_views
            WHERE product_id = ?
        """, (product_id,)).fetchone()

        return int(row["total"] or 0)


class ChatSettings:

    @staticmethod
    def get(user_id):

        db = get_db()

        row = db.execute("""
            SELECT *
            FROM chat_settings
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if row:
            return row

        db.execute("""
            INSERT OR IGNORE INTO chat_settings
            (
                user_id,
                voice_type,
                voice_enabled,
                language,
                style
            )
            VALUES (?, 'female', 1, 'ar', 'friendly')
        """, (user_id,))

        db.commit()

        return db.execute("""
            SELECT *
            FROM chat_settings
            WHERE user_id = ?
        """, (user_id,)).fetchone()

    @staticmethod
    def update(user_id, **data):

        allowed = [
            "voice_type",
            "voice_enabled",
            "language",
            "style"
        ]

        fields = []
        values = []

        for key in allowed:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])

        if not fields:
            return

        values.append(user_id)

        db = get_db()

        db.execute("""
            INSERT OR IGNORE INTO chat_settings
            (user_id)
            VALUES (?)
        """, (user_id,))

        db.execute(
            f"""
            UPDATE chat_settings
            SET {', '.join(fields)}
            WHERE user_id = ?
            """,
            values
        )

        db.commit()
