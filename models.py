# models.py
# ============================================================
# DZ MARKET 🇩🇿
# Database Models / Data Access Layer
# ============================================================

import secrets
import string

from database import get_db


# ============================================================
# HELPERS
# ============================================================

def generate_code(prefix="DZ"):
    alphabet = string.ascii_uppercase + string.digits
    random_part = "".join(
        secrets.choice(alphabet) for _ in range(8)
    )
    return f"{prefix}-{random_part}"


def _execute(query, params=(), commit=False):
    db = get_db()
    cursor = db.execute(query, params)

    if commit:
        db.commit()

    return cursor


def _fetchone(query, params=()):
    return _execute(query, params).fetchone()


def _fetchall(query, params=()):
    return _execute(query, params).fetchall()


# ============================================================
# USER
# ============================================================

class User:

    @staticmethod
    def create(
        full_name,
        email,
        password_hash,
        phone=None,
        role="buyer",
        wilaya=None,
        municipality=None,
        seller_activity_type=None,
        seller_verification_note=None,
        referral_code=None,
        referred_by=None
    ):
        if role not in ("buyer", "seller", "admin"):
            raise ValueError("Invalid user role.")

        if not referral_code:
            referral_code = generate_code("DZ")

        cursor = _execute(
            """
            INSERT INTO users (
                full_name,
                email,
                phone,
                password,
                role,
                wilaya,
                municipality,
                seller_activity_type,
                seller_verification_note,
                referral_code,
                referred_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name.strip(),
                email.strip().lower(),
                phone,
                password_hash,
                role,
                wilaya,
                municipality,
                seller_activity_type,
                seller_verification_note,
                referral_code,
                referred_by
            ),
            commit=True
        )

        return User.find_by_id(cursor.lastrowid)

    @staticmethod
    def find_by_email(email):
        if not email:
            return None

        return _fetchone(
            """
            SELECT *
            FROM users
            WHERE email = ?
            LIMIT 1
            """,
            (email.strip().lower(),)
        )

    @staticmethod
    def find_by_id(user_id):
        return _fetchone(
            """
            SELECT *
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_id,)
        )

    @staticmethod
    def find_by_referral_code(code):
        return _fetchone(
            """
            SELECT *
            FROM users
            WHERE referral_code = ?
            LIMIT 1
            """,
            (code,)
        )

    @staticmethod
    def update_profile(
        user_id,
        full_name=None,
        phone=None,
        bio=None,
        wilaya=None,
        municipality=None,
        avatar=None
    ):
        user = User.find_by_id(user_id)

        if not user:
            return None

        _execute(
            """
            UPDATE users
            SET
                full_name = ?,
                phone = ?,
                bio = ?,
                wilaya = ?,
                municipality = ?,
                avatar = ?
            WHERE id = ?
            """,
            (
                full_name if full_name is not None else user["full_name"],
                phone if phone is not None else user["phone"],
                bio if bio is not None else user["bio"],
                wilaya if wilaya is not None else user["wilaya"],
                municipality
                if municipality is not None
                else user["municipality"],
                avatar if avatar is not None else user["avatar"],
                user_id
            ),
            commit=True
        )

        return User.find_by_id(user_id)

    @staticmethod
    def update_settings(
        user_id,
        language=None
    ):
        user = User.find_by_id(user_id)

        if not user:
            return None

        language = language or user["language"]

        if language not in ("ar", "fr", "en", "tzm"):
            raise ValueError("Invalid language.")

        _execute(
            """
            UPDATE users
            SET language = ?
            WHERE id = ?
            """,
            (language, user_id),
            commit=True
        )

        return User.find_by_id(user_id)

    @staticmethod
    def verify_phone(user_id):
        _execute(
            """
            UPDATE users
            SET phone_verified = 1
            WHERE id = ?
            """,
            (user_id,),
            commit=True
        )

        return User.find_by_id(user_id)

    @staticmethod
    def set_seller_verification(
        user_id,
        status,
        note=None
    ):
        if status not in ("pending", "approved", "rejected"):
            raise ValueError("Invalid seller verification status.")

        _execute(
            """
            UPDATE users
            SET
                seller_verification_status = ?,
                seller_verification_note = ?
            WHERE id = ?
            """,
            (status, note, user_id),
            commit=True
        )

        return User.find_by_id(user_id)


# ============================================================
# STORE
# ============================================================

class Store:

    @staticmethod
    def create(
        user_id,
        name,
        description=None,
        phone=None,
        wilaya=None,
        municipality=None,
        logo=None,
        cover_image=None
    ):
        cursor = _execute(
            """
            INSERT INTO stores (
                user_id,
                name,
                description,
                phone,
                wilaya,
                municipality,
                logo,
                cover_image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name.strip(),
                description,
                phone,
                wilaya,
                municipality,
                logo,
                cover_image
            ),
            commit=True
        )

        return Store.find_by_id(cursor.lastrowid)

    @staticmethod
    def find_by_id(store_id):
        return _fetchone(
            """
            SELECT *
            FROM stores
            WHERE id = ?
            LIMIT 1
            """,
            (store_id,)
        )

    @staticmethod
    def find_by_user_id(user_id):
        return _fetchone(
            """
            SELECT *
            FROM stores
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,)
        )

    @staticmethod
    def update(
        store_id,
        name=None,
        description=None,
        phone=None,
        wilaya=None,
        municipality=None,
        logo=None,
        cover_image=None
    ):
        store = Store.find_by_id(store_id)

        if not store:
            return None

        _execute(
            """
            UPDATE stores
            SET
                name = ?,
                description = ?,
                phone = ?,
                wilaya = ?,
                municipality = ?,
                logo = ?,
                cover_image = ?
            WHERE id = ?
            """,
            (
                name if name is not None else store["name"],
                description
                if description is not None
                else store["description"],
                phone if phone is not None else store["phone"],
                wilaya if wilaya is not None else store["wilaya"],
                municipality
                if municipality is not None
                else store["municipality"],
                logo if logo is not None else store["logo"],
                cover_image
                if cover_image is not None
                else store["cover_image"],
                store_id
            ),
            commit=True
        )

        return Store.find_by_id(store_id)

    @staticmethod
    def public_profile(store_id):
        return _fetchone(
            """
            SELECT
                s.*,
                u.full_name,
                u.seller_verification_status
            FROM stores s
            JOIN users u
                ON u.id = s.user_id
            WHERE s.id = ?
            LIMIT 1
            """,
            (store_id,)
        )

    @staticmethod
    def increment_sales(store_id, amount=1):
        _execute(
            """
            UPDATE stores
            SET total_sales = total_sales + ?
            WHERE id = ?
            """,
            (amount, store_id),
            commit=True
        )

    @staticmethod
    def update_trust_score(store_id, score):
        score = max(0, min(float(score), 100))

        _execute(
            """
            UPDATE stores
            SET trust_score = ?
            WHERE id = ?
            """,
            (score, store_id),
            commit=True
        )

        return Store.find_by_id(store_id)

    @staticmethod
    def set_verification(
        store_id,
        status,
        note=None
    ):
        if status not in ("pending", "approved", "rejected"):
            raise ValueError("Invalid store verification status.")

        _execute(
            """
            UPDATE stores
            SET
                verification_status = ?,
                verification_note = ?
            WHERE id = ?
            """,
            (status, note, store_id),
            commit=True
        )

        return Store.find_by_id(store_id)


# ============================================================
# PRODUCT
# ============================================================

class Product:

    VALID_AVAILABILITY = (
        "available_now",
        "made_to_order",
        "both"
    )

    @staticmethod
    def create(
        store_id,
        name,
        description=None,
        price=0,
        discount=0,
        quantity=0,
        category=None,
        brand=None,
        images=None,
        video=None,
        delivery_wilayas=None,
        availability_type="available_now",
        preparation_time_minutes=0,
        colors=None,
        sizes=None
    ):
        if availability_type not in Product.VALID_AVAILABILITY:
            raise ValueError("Invalid availability type.")

        price = float(price)
        discount = float(discount)
        quantity = int(quantity)
        preparation_time_minutes = int(
            preparation_time_minutes or 0
        )

        if price < 0:
            raise ValueError("Price cannot be negative.")

        if discount < 0:
            raise ValueError("Discount cannot be negative.")

        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")

        if preparation_time_minutes < 0:
            raise ValueError(
                "Preparation time cannot be negative."
            )

        cursor = _execute(
            """
            INSERT INTO products (
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
                delivery_wilayas,
                availability_type,
                preparation_time_minutes,
                colors,
                sizes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                store_id,
                name.strip(),
                description,
                price,
                discount,
                quantity,
                category,
                brand,
                images,
                video,
                delivery_wilayas,
                availability_type,
                preparation_time_minutes,
                colors,
                sizes
            ),
            commit=True
        )

        return Product.find_by_id(cursor.lastrowid)

    @staticmethod
    def find_by_id(product_id):
        return _fetchone(
            """
            SELECT
                p.*,
                s.name AS store_name,
                s.trust_score,
                s.verification_status AS store_verification_status
            FROM products p
            JOIN stores s
                ON s.id = p.store_id
            WHERE p.id = ?
            LIMIT 1
            """,
            (product_id,)
        )

    @staticmethod
    def by_store(store_id, active_only=False):
        query = """
            SELECT *
            FROM products
            WHERE store_id = ?
        """

        params = [store_id]

        if active_only:
            query += " AND active = 1"

        query += """
            ORDER BY created_at DESC, id DESC
        """

        return _fetchall(query, params)

    @staticmethod
    def update(
        product_id,
        name=None,
        description=None,
        price=None,
        discount=None,
        quantity=None,
        category=None,
        brand=None,
        images=None,
        video=None,
        delivery_wilayas=None,
        availability_type=None,
        preparation_time_minutes=None,
        colors=None,
        sizes=None,
        active=None
    ):
        product = Product.find_by_id(product_id)

        if not product:
            return None

        current_availability = product["availability_type"]

        availability_type = (
            availability_type
            if availability_type is not None
            else current_availability
        )

        if availability_type not in Product.VALID_AVAILABILITY:
            raise ValueError("Invalid availability type.")

        quantity = (
            int(quantity)
            if quantity is not None
            else product["quantity"]
        )

        price = (
            float(price)
            if price is not None
            else product["price"]
        )

        discount = (
            float(discount)
            if discount is not None
            else product["discount"]
        )

        preparation_time_minutes = (
            int(preparation_time_minutes)
            if preparation_time_minutes is not None
            else product["preparation_time_minutes"]
        )

        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")

        if price < 0:
            raise ValueError("Price cannot be negative.")

        if discount < 0:
            raise ValueError("Discount cannot be negative.")

        if preparation_time_minutes < 0:
            raise ValueError(
                "Preparation time cannot be negative."
            )

        _execute(
            """
            UPDATE products
            SET
                name = ?,
                description = ?,
                price = ?,
                discount = ?,
                quantity = ?,
                category = ?,
                brand = ?,
                images = ?,
                video = ?,
                delivery_wilayas = ?,
                availability_type = ?,
                preparation_time_minutes = ?,
                colors = ?,
                sizes = ?,
                active = ?
            WHERE id = ?
            """,
            (
                name if name is not None else product["name"],
                description
                if description is not None
                else product["description"],
                price,
                discount,
                quantity,
                category
                if category is not None
                else product["category"],
                brand if brand is not None else product["brand"],
                images if images is not None else product["images"],
                video if video is not None else product["video"],
                delivery_wilayas
                if delivery_wilayas is not None
                else product["delivery_wilayas"],
                availability_type,
                preparation_time_minutes,
                colors if colors is not None else product["colors"],
                sizes if sizes is not None else product["sizes"],
                int(active)
                if active is not None
                else product["active"],
                product_id
            ),
            commit=True
        )

        return Product.find_by_id(product_id)

    @staticmethod
    def update_rating(product_id):
        result = _fetchone(
            """
            SELECT
                COALESCE(AVG(rating), 0) AS average_rating,
                COUNT(*) AS review_count
            FROM reviews
            WHERE product_id = ?
            """,
            (product_id,)
        )

        rating = float(result["average_rating"] or 0)
        review_count = int(result["review_count"] or 0)

        _execute(
            """
            UPDATE products
            SET
                rating = ?,
                reviews_count = ?
            WHERE id = ?
            """,
            (
                round(rating, 2),
                review_count,
                product_id
            ),
            commit=True
        )

        return Product.find_by_id(product_id)

    @staticmethod
    def decrease_stock(product_id, quantity):
        quantity = int(quantity)

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        db = get_db()

        cursor = db.execute(
            """
            UPDATE products
            SET quantity = quantity - ?
            WHERE id = ?
              AND quantity >= ?
              AND availability_type IN ('available_now', 'both')
            """,
            (
                quantity,
                product_id,
                quantity
            )
        )

        db.commit()

        return cursor.rowcount == 1


# ============================================================
# FAVORITES
# ============================================================

class Favorite:

    @staticmethod
    def add(user_id, product_id):
        _execute(
            """
            INSERT OR IGNORE INTO favorites (
                user_id,
                product_id
            )
            VALUES (?, ?)
            """,
            (user_id, product_id),
            commit=True
        )

    @staticmethod
    def remove(user_id, product_id):
        _execute(
            """
            DELETE FROM favorites
            WHERE user_id = ?
              AND product_id = ?
            """,
            (user_id, product_id),
            commit=True
        )

    @staticmethod
    def all(user_id):
        return _fetchall(
            """
            SELECT
                p.*,
                s.name AS store_name
            FROM favorites f
            JOIN products p
                ON p.id = f.product_id
            JOIN stores s
                ON s.id = p.store_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
            """,
            (user_id,)
        )

    @staticmethod
    def exists(user_id, product_id):
        return _fetchone(
            """
            SELECT id
            FROM favorites
            WHERE user_id = ?
              AND product_id = ?
            LIMIT 1
            """,
            (user_id, product_id)
        ) is not None


# ============================================================
# CART
# ============================================================

class Cart:

    VALID_MODES = (
        "ready_stock",
        "made_to_order"
    )

    @staticmethod
    def add(
        user_id,
        product_id,
        quantity=1,
        purchase_mode="ready_stock"
    ):
        quantity = int(quantity)

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        if purchase_mode not in Cart.VALID_MODES:
            raise ValueError("Invalid purchase mode.")

        product = Product.find_by_id(product_id)

        if not product:
            raise ValueError("Product not found.")

        availability = product["availability_type"]

        if availability == "available_now":
            purchase_mode = "ready_stock"

        elif availability == "made_to_order":
            purchase_mode = "made_to_order"

        elif availability == "both":
            pass

        existing = _fetchone(
            """
            SELECT *
            FROM cart_items
            WHERE user_id = ?
              AND product_id = ?
              AND purchase_mode = ?
            LIMIT 1
            """,
            (
                user_id,
                product_id,
                purchase_mode
            )
        )

        if existing:
            new_quantity = existing["quantity"] + quantity
        else:
            new_quantity = quantity

        if purchase_mode == "ready_stock":
            if new_quantity > product["quantity"]:
                raise ValueError(
                    "Requested quantity exceeds available stock."
                )

        if existing:
            _execute(
                """
                UPDATE cart_items
                SET quantity = ?
                WHERE id = ?
                """,
                (
                    new_quantity,
                    existing["id"]
                ),
                commit=True
            )

        else:
            _execute(
                """
                INSERT INTO cart_items (
                    user_id,
                    product_id,
                    quantity,
                    purchase_mode
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    product_id,
                    new_quantity,
                    purchase_mode
                ),
                commit=True
            )

    @staticmethod
    def update(
        user_id,
        cart_item_id,
        quantity
    ):
        quantity = int(quantity)

        if quantity <= 0:
            return Cart.remove(
                user_id,
                cart_item_id
            )

        item = _fetchone(
            """
            SELECT
                c.*,
                p.quantity AS available_quantity,
                p.availability_type
            FROM cart_items c
            JOIN products p
                ON p.id = c.product_id
            WHERE c.id = ?
              AND c.user_id = ?
            LIMIT 1
            """,
            (
                cart_item_id,
                user_id
            )
        )

        if not item:
            return False

        if (
            item["purchase_mode"] == "ready_stock"
            and quantity > item["available_quantity"]
        ):
            raise ValueError(
                "Requested quantity exceeds available stock."
            )

        _execute(
            """
            UPDATE cart_items
            SET quantity = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                quantity,
                cart_item_id,
                user_id
            ),
            commit=True
        )

        return True

    @staticmethod
    def remove(user_id, cart_item_id):
        _execute(
            """
            DELETE FROM cart_items
            WHERE id = ?
              AND user_id = ?
            """,
            (
                cart_item_id,
                user_id
            ),
            commit=True
        )

    @staticmethod
    def clear(user_id):
        _execute(
            """
            DELETE FROM cart_items
            WHERE user_id = ?
            """,
            (user_id,),
            commit=True
        )

    @staticmethod
    def get_items(user_id):
        return _fetchall(
            """
            SELECT
                c.id,
                c.user_id,
                c.product_id,
                c.quantity,
                c.purchase_mode,

                p.name,
                p.price,
                p.discount,
                p.quantity AS available_quantity,
                p.images,
                p.video,
                p.availability_type,
                p.preparation_time_minutes,

                s.id AS store_id,
                s.name AS store_name

            FROM cart_items c

            JOIN products p
                ON p.id = c.product_id

            JOIN stores s
                ON s.id = p.store_id

            WHERE c.user_id = ?

            ORDER BY c.created_at DESC
            """,
            (user_id,)
        )


# ============================================================
# ORDER
# ============================================================

class Order:

    ALLOWED_STATUSES = (
        "pending",
        "confirmed",
        "preparing",
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
        delivery_address,
        delivery_wilaya,
        delivery_phone,
        status="pending"
    ):
        if status not in Order.ALLOWED_STATUSES:
            raise ValueError("Invalid order status.")

        cursor = _execute(
            """
            INSERT INTO orders (
                user_id,
                total_amount,
                delivery_address,
                delivery_wilaya,
                delivery_phone,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                float(total_amount),
                delivery_address,
                delivery_wilaya,
                delivery_phone,
                status
            ),
            commit=True
        )

        return Order.find_by_id(cursor.lastrowid)

    @staticmethod
    def find_by_id(order_id):
        return _fetchone(
            """
            SELECT *
            FROM orders
            WHERE id = ?
            LIMIT 1
            """,
            (order_id,)
        )

    @staticmethod
    def by_user(user_id):
        return _fetchall(
            """
            SELECT *
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,)
        )

    @staticmethod
    def update_status(order_id, status):
        if status not in Order.ALLOWED_STATUSES:
            raise ValueError("Invalid order status.")

        _execute(
            """
            UPDATE orders
            SET
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status,
                order_id
            ),
            commit=True
        )

        return Order.find_by_id(order_id)

    @staticmethod
    def confirm_receipt(order_id, user_id):
        order = _fetchone(
            """
            SELECT *
            FROM orders
            WHERE id = ?
              AND user_id = ?
            LIMIT 1
            """,
            (
                order_id,
                user_id
            )
        )

        if not order:
            return None

        if order["status"] != "delivered":
            raise ValueError(
                "Order must be delivered before receipt confirmation."
            )

        return Order.update_status(
            order_id,
            "delivered"
        )


# ============================================================
# ORDER ITEM
# ============================================================

class OrderItem:

    @staticmethod
    def create(
        order_id,
        product_id,
        store_id,
        quantity,
        price,
        purchase_mode="ready_stock",
        preparation_time_minutes=0
    ):
        if purchase_mode not in (
            "ready_stock",
            "made_to_order"
        ):
            raise ValueError("Invalid purchase mode.")

        cursor = _execute(
            """
            INSERT INTO order_items (
                order_id,
                product_id,
                store_id,
                quantity,
                price,
                purchase_mode,
                preparation_time_minutes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                product_id,
                store_id,
                int(quantity),
                float(price),
                purchase_mode,
                int(preparation_time_minutes or 0)
            ),
            commit=True
        )

        return _fetchone(
            """
            SELECT *
            FROM order_items
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        )

    @staticmethod
    def by_order(order_id):
        return _fetchall(
            """
            SELECT
                oi.*,
                p.name AS product_name,
                p.images,
                s.name AS store_name
            FROM order_items oi
            JOIN products p
                ON p.id = oi.product_id
            JOIN stores s
                ON s.id = oi.store_id
            WHERE oi.order_id = ?
            ORDER BY oi.id ASC
            """,
            (order_id,)
        )


# ============================================================
# REVIEW
# ============================================================

class Review:

    @staticmethod
    def can_review(
        user_id,
        product_id,
        order_id
    ):
        order = _fetchone(
            """
            SELECT id
            FROM orders
            WHERE id = ?
              AND user_id = ?
              AND status = 'delivered'
            LIMIT 1
            """,
            (
                order_id,
                user_id
            )
        )

        if not order:
            return False

        purchased = _fetchone(
            """
            SELECT id
            FROM order_items
            WHERE order_id = ?
              AND product_id = ?
            LIMIT 1
            """,
            (
                order_id,
                product_id
            )
        )

        if not purchased:
            return False

        already_reviewed = _fetchone(
            """
            SELECT id
            FROM reviews
            WHERE user_id = ?
              AND product_id = ?
              AND order_id = ?
            LIMIT 1
            """,
            (
                user_id,
                product_id,
                order_id
            )
        )

        return already_reviewed is None

    @staticmethod
    def create(
        user_id,
        product_id,
        order_id,
        rating,
        comment=None,
        order_item_id=None
    ):
        rating = int(rating)

        if rating < 1 or rating > 5:
            raise ValueError(
                "Rating must be between 1 and 5."
            )

        if not Review.can_review(
            user_id,
            product_id,
            order_id
        ):
            raise ValueError(
                "You can only review a purchased and delivered product."
            )

        cursor = _execute(
            """
            INSERT INTO reviews (
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
            ),
            commit=True
        )

        Product.update_rating(product_id)

        return _fetchone(
            """
            SELECT *
            FROM reviews
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        )

    @staticmethod
    def by_product(product_id):
        return _fetchall(
            """
            SELECT
                r.*,
                u.full_name,
                u.avatar
            FROM reviews r
            JOIN users u
                ON u.id = r.user_id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC
            """,
            (product_id,)
        )


# ============================================================
# STORE FOLLOWERS
# ============================================================

class StoreFollower:

    @staticmethod
    def follow(user_id, store_id):
        _execute(
            """
            INSERT OR IGNORE INTO store_followers (
                user_id,
                store_id
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                store_id
            ),
            commit=True
        )

    @staticmethod
    def unfollow(user_id, store_id):
        _execute(
            """
            DELETE FROM store_followers
            WHERE user_id = ?
              AND store_id = ?
            """,
            (
                user_id,
                store_id
            ),
            commit=True
        )

    @staticmethod
    def count(store_id):
        result = _fetchone(
            """
            SELECT COUNT(*) AS total
            FROM store_followers
            WHERE store_id = ?
            """,
            (store_id,)
        )

        return int(result["total"])

    @staticmethod
    def is_following(user_id, store_id):
        return _fetchone(
            """
            SELECT id
            FROM store_followers
            WHERE user_id = ?
              AND store_id = ?
            LIMIT 1
            """,
            (
                user_id,
                store_id
            )
        ) is not None


# ============================================================
# MESSAGES
# ============================================================

class Message:

    @staticmethod
    def create(
        sender_id,
        receiver_id,
        body,
        product_id=None
    ):
        body = (body or "").strip()

        if not body:
            raise ValueError(
                "Message cannot be empty."
            )

        # Prevent messaging blocked users.
        blocked = _fetchone(
            """
            SELECT id
            FROM blocked_users
            WHERE
                (
                    user_id = ?
                    AND blocked_user_id = ?
                )
                OR
                (
                    user_id = ?
                    AND blocked_user_id = ?
                )
            LIMIT 1
            """,
            (
                sender_id,
                receiver_id,
                receiver_id,
                sender_id
            )
        )

        if blocked:
            raise ValueError(
                "Messaging is unavailable between these users."
            )

        cursor = _execute(
            """
            INSERT INTO messages (
                sender_id,
                receiver_id,
                product_id,
                body
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                sender_id,
                receiver_id,
                product_id,
                body
            ),
            commit=True
        )

        return _fetchone(
            """
            SELECT *
            FROM messages
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        )

    @staticmethod
    def between(
        user_id,
        other_user_id,
        product_id=None
    ):
        query = """
            SELECT
                m.*,
                u.full_name AS sender_name
            FROM messages m
            JOIN users u
                ON u.id = m.sender_id
            WHERE
                (
                    m.sender_id = ?
                    AND m.receiver_id = ?
                )
                OR
                (
                    m.sender_id = ?
                    AND m.receiver_id = ?
                )
        """

        params = [
            user_id,
            other_user_id,
            other_user_id,
            user_id
        ]

        if product_id is not None:
            query += """
                AND m.product_id = ?
            """
            params.append(product_id)

        query += """
            ORDER BY m.created_at ASC, m.id ASC
        """

        return _fetchall(
            query,
            params
        )

    @staticmethod
    def conversations(user_id):
        return _fetchall(
            """
            SELECT
                other.id AS other_user_id,
                other.full_name AS other_name,
                other.avatar AS other_avatar,
                m.body AS last_message,
                m.created_at AS last_message_at,

                (
                    SELECT COUNT(*)
                    FROM messages unread
                    WHERE unread.sender_id = other.id
                      AND unread.receiver_id = ?
                      AND unread.is_read = 0
                ) AS unread_count

            FROM messages m

            JOIN users other
                ON other.id =
                    CASE
                        WHEN m.sender_id = ?
                        THEN m.receiver_id
                        ELSE m.sender_id
                    END

            WHERE
                m.sender_id = ?
                OR m.receiver_id = ?

            AND m.id = (
                SELECT MAX(m2.id)
                FROM messages m2
                WHERE
                    (
                        m2.sender_id = m.sender_id
                        AND m2.receiver_id = m.receiver_id
                    )
                    OR
                    (
                        m2.sender_id = m.receiver_id
                        AND m2.receiver_id = m.sender_id
                    )
            )

            ORDER BY m.created_at DESC
            """,
            (
                user_id,
                user_id,
                user_id,
                user_id
            )
        )

    @staticmethod
    def mark_as_read(
        receiver_id,
        sender_id,
        product_id=None
    ):
        query = """
            UPDATE messages
            SET is_read = 1
            WHERE receiver_id = ?
              AND sender_id = ?
              AND is_read = 0
        """

        params = [
            receiver_id,
            sender_id
        ]

        if product_id is not None:
            query += " AND product_id = ?"
            params.append(product_id)

        _execute(
            query,
            params,
            commit=True
        )


# ============================================================
# NOTIFICATIONS
# ============================================================

class Notification:

    @staticmethod
    def create(
        user_id,
        title,
        body
    ):
        cursor = _execute(
            """
            INSERT INTO notifications (
                user_id,
                title,
                message
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                title,
                body
            ),
            commit=True
        )

        return _fetchone(
            """
            SELECT *
            FROM notifications
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        )

    @staticmethod
    def by_user(user_id):
        return _fetchall(
            """
            SELECT *
            FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,)
        )

    @staticmethod
    def unread_count(user_id):
        result = _fetchone(
            """
            SELECT COUNT(*) AS total
            FROM notifications
            WHERE user_id = ?
              AND is_read = 0
            """,
            (user_id,)
        )

        return int(result["total"])

    @staticmethod
    def mark_as_read(
        notification_id,
        user_id
    ):
        _execute(
            """
            UPDATE notifications
            SET is_read = 1
            WHERE id = ?
              AND user_id = ?
            """,
            (
                notification_id,
                user_id
            ),
            commit=True
        )


# ============================================================
# COMPLAINTS
# ============================================================

class Complaint:

    VALID_STATUSES = (
        "open",
        "in_review",
        "resolved",
        "closed"
    )

    @staticmethod
    def create(
        user_id,
        subject,
        body,
        order_id=None
    ):
        cursor = _execute(
            """
            INSERT INTO complaints (
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
                body
            ),
            commit=True
        )

        return _fetchone(
            """
            SELECT *
            FROM complaints
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        )

    @staticmethod
    def by_user(user_id):
        return _fetchall(
            """
            SELECT *
            FROM complaints
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,)
        )

    @staticmethod
    def update_status(
        complaint_id,
        status
    ):
        if status not in Complaint.VALID_STATUSES:
            raise ValueError(
                "Invalid complaint status."
            )

        _execute(
            """
            UPDATE complaints
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                complaint_id
            ),
            commit=True
        )


# ============================================================
# BLOCKED USERS
# ============================================================

class BlockedUser:

    @staticmethod
    def block(
        user_id,
        blocked_user_id
    ):
        if user_id == blocked_user_id:
            raise ValueError(
                "You cannot block yourself."
            )

        _execute(
            """
            INSERT OR IGNORE INTO blocked_users (
                user_id,
                blocked_user_id
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                blocked_user_id
            ),
            commit=True
        )

    @staticmethod
    def unblock(
        user_id,
        blocked_user_id
    ):
        _execute(
            """
            DELETE FROM blocked_users
            WHERE user_id = ?
              AND blocked_user_id = ?
            """,
            (
                user_id,
                blocked_user_id
            ),
            commit=True
        )

    @staticmethod
    def is_blocked(
        user_id,
        other_user_id
    ):
        return _fetchone(
            """
            SELECT id
            FROM blocked_users
            WHERE user_id = ?
              AND blocked_user_id = ?
            LIMIT 1
            """,
            (
                user_id,
                other_user_id
            )
        ) is not None


# ============================================================
# REWARD CARDS
# ============================================================

class RewardCard:

    @staticmethod
    def create(
        user_id,
        reward_type,
        reward_value=0,
        expires_at=None
    ):
        code = generate_code("CARD")

        cursor = _execute(
            """
            INSERT INTO reward_cards (
                user_id,
                code,
                reward_type,
                reward_value,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                code,
                reward_type,
                float(reward_value),
                expires_at
            ),
            commit=True
        )

        return _fetchone(
            """
            SELECT *
            FROM reward_cards
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        )

    @staticmethod
    def by_user(user_id):
        return _fetchall(
            """
            SELECT *
            FROM reward_cards
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        )

    @staticmethod
    def find_by_code(code):
        return _fetchone(
            """
            SELECT *
            FROM reward_cards
            WHERE code = ?
            LIMIT 1
            """,
            (code,)
        )

    @staticmethod
    def use(code, user_id):
        card = _fetchone(
            """
            SELECT *
            FROM reward_cards
            WHERE code = ?
              AND user_id = ?
              AND used = 0
            LIMIT 1
            """,
            (
                code,
                user_id
            )
        )

        if not card:
            return False

        _execute(
            """
            UPDATE reward_cards
            SET used = 1
            WHERE id = ?
              AND user_id = ?
              AND used = 0
            """,
            (
                card["id"],
                user_id
            ),
            commit=True
        )

        return True


# ============================================================
# REFERRALS
# ============================================================

class Referral:

    @staticmethod
    def create(
        inviter_id,
        invited_user_id
    ):
        if inviter_id == invited_user_id:
            raise ValueError(
                "A user cannot refer themselves."
            )

        cursor = _execute(
            """
            INSERT INTO referrals (
                inviter_id,
                invited_user_id
            )
            VALUES (?, ?)
            """,
            (
                inviter_id,
                invited_user_id
            ),
            commit=True
        )

        return _fetchone(
            """
            SELECT *
            FROM referrals
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        )

    @staticmethod
    def by_inviter(inviter_id):
        return _fetchall(
            """
            SELECT
                r.*,
                u.full_name,
                u.email
            FROM referrals r
            JOIN users u
                ON u.id = r.invited_user_id
            WHERE r.inviter_id = ?
            ORDER BY r.created_at DESC
            """,
            (inviter_id,)
        )

    @staticmethod
    def complete(invited_user_id):
        _execute(
            """
            UPDATE referrals
            SET
                status = 'completed',
                completed_at = CURRENT_TIMESTAMP
            WHERE invited_user_id = ?
              AND status = 'pending'
            """,
            (invited_user_id,),
            commit=True
        )


# ============================================================
# REWARD MILESTONES
# ============================================================

class RewardMilestone:

    @staticmethod
    def completed_orders(user_id):
        result = _fetchone(
            """
            SELECT COUNT(*) AS total
            FROM orders
            WHERE user_id = ?
              AND status = 'delivered'
            """,
            (user_id,)
        )

        return int(result["total"])

    @staticmethod
    def has_achieved(
        user_id,
        milestone_type,
        milestone_value
    ):
        return _fetchone(
            """
            SELECT id
            FROM reward_milestones
            WHERE user_id = ?
              AND milestone_type = ?
              AND milestone_value = ?
              AND achieved = 1
            LIMIT 1
            """,
            (
                user_id,
                milestone_type,
                milestone_value
            )
        ) is not None

    @staticmethod
    def grant_milestone(
        user_id,
        milestone_type,
        milestone_value
    ):
        _execute(
            """
            INSERT INTO reward_milestones (
                user_id,
                milestone_type,
                milestone_value,
                achieved,
                achieved_at
            )
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)

            ON CONFLICT(
                user_id,
                milestone_type,
                milestone_value
            )
            DO UPDATE SET
                achieved = 1,
                achieved_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                milestone_type,
                milestone_value
            ),
            commit=True
        )


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
        cursor = _execute(
            """
            INSERT INTO price_alerts (
                user_id,
                product_id,
                target_price
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                product_id,
                float(target_price)
            ),
            commit=True
        )

        return _fetchone(
            """
            SELECT *
            FROM price_alerts
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        )

    @staticmethod
    def by_user(user_id):
        return _fetchall(
            """
            SELECT
                pa.*,
                p.name,
                p.price,
                p.images
            FROM price_alerts pa
            JOIN products p
                ON p.id = pa.product_id
            WHERE pa.user_id = ?
            ORDER BY pa.created_at DESC
            """,
            (user_id,)
        )


# ============================================================
# PRODUCT VIEWS
# ============================================================

class ProductView:

    @staticmethod
    def add(
        product_id,
        user_id=None
    ):
        _execute(
            """
            INSERT INTO product_views (
                product_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                product_id,
                user_id
            ),
            commit=True
        )

        _execute(
            """
            UPDATE products
            SET views = views + 1
            WHERE id = ?
            """,
            (product_id,),
            commit=True
        )

    @staticmethod
    def count(product_id):
        result = _fetchone(
            """
            SELECT COUNT(*) AS total
            FROM product_views
            WHERE product_id = ?
            """,
            (product_id,)
        )

        return int(result["total"])


# ============================================================
# CHAT SETTINGS
# ============================================================

class ChatSettings:

    VALID_VOICE_TYPES = (
        "female",
        "male"
    )

    VALID_LANGUAGES = (
        "ar",
        "dz",
        "fr",
        "en"
    )

    VALID_STYLES = (
        "friendly",
        "youthful",
        "funny",
        "professional",
        "darija"
    )

    @staticmethod
    def get(user_id):

        settings = _fetchone(
            """
            SELECT *
            FROM chat_settings
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,)
        )

        if settings:
            return settings

        _execute(
            """
            INSERT INTO chat_settings (
                user_id
            )
            VALUES (?)
            """,
            (user_id,),
            commit=True
        )

        return _fetchone(
            """
            SELECT *
            FROM chat_settings
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,)
        )

    @staticmethod
    def update(
        user_id,
        voice_type=None,
        voice_enabled=None,
        language=None,
        style=None
    ):
        current = ChatSettings.get(user_id)

        voice_type = (
            voice_type
            if voice_type is not None
            else current["voice_type"]
        )

        voice_enabled = (
            int(voice_enabled)
            if voice_enabled is not None
            else current["voice_enabled"]
        )

        language = (
            language
            if language is not None
            else current["language"]
        )

        style = (
            style
            if style is not None
            else current["style"]
        )

        if voice_type not in ChatSettings.VALID_VOICE_TYPES:
            raise ValueError("Invalid voice type.")

        if language not in ChatSettings.VALID_LANGUAGES:
            raise ValueError("Invalid chat language.")

        if style not in ChatSettings.VALID_STYLES:
            raise ValueError("Invalid chat style.")

        _execute(
            """
            UPDATE chat_settings
            SET
                voice_type = ?,
                voice_enabled = ?,
                language = ?,
                style = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (
                voice_type,
                voice_enabled,
                language,
                style,
                user_id
            ),
            commit=True
        )

        return ChatSettings.get(user_id)
