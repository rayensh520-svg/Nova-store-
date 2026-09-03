# database.py
# ============================================================
# DZ MARKET 🇩🇿
# Database Layer
# SQLite foundation - structured for future PostgreSQL migration
# ============================================================

import os
import secrets
import string
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = Path(
    os.getenv("DZMARKET_DATABASE", BASE_DIR / "dzmarket.db")
)


# ============================================================
# HELPERS
# ============================================================

def generate_code(prefix="DZ"):
    """Generate a unique-looking public code."""
    alphabet = string.ascii_uppercase + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"{prefix}-{random_part}"


def get_connection():
    """
    Create a SQLite connection configured for the application.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    # Foreign keys
    connection.execute("PRAGMA foreign_keys = ON")

    # Better concurrent-read behavior
    connection.execute("PRAGMA journal_mode = WAL")

    # Balanced durability/performance
    connection.execute("PRAGMA synchronous = NORMAL")

    # Wait when database is temporarily locked
    connection.execute("PRAGMA busy_timeout = 30000")

    return connection


# ============================================================
# FLASK DATABASE HELPER
# ============================================================

def get_db():
    """
    Request-safe database connection.

    models.py and routes.py can use this function.
    A new connection is created per request/thread.
    """

    try:
        from flask import g

        if "db" not in g:
            g.db = get_connection()

        return g.db

    except RuntimeError:
        # Allows models/database utilities to work outside
        # an active Flask request when necessary.
        return get_connection()


def close_db(exception=None):
    """
    Close the Flask database connection after the request.
    """

    try:
        from flask import g

        db = g.pop("db", None)

        if db is not None:
            db.close()

    except RuntimeError:
        pass


def init_app(app):
    """
    Register database lifecycle hooks with Flask.
    """

    app.teardown_appcontext(close_db)


# ============================================================
# MIGRATION HELPERS
# ============================================================

def add_column_if_missing(
    connection,
    table_name,
    column_name,
    column_definition
):
    """
    Safely add a column when an older database already exists.
    """

    columns = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    existing_columns = {
        column["name"]
        for column in columns
    }

    if column_name not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column_name} {column_definition}"
        )


def table_exists(connection, table_name):
    result = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,)
    ).fetchone()

    return result is not None


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database():
    """
    Create all DZ MARKET tables and apply lightweight migrations.
    """

    connection = get_connection()

    try:

        # ====================================================
        # USERS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                full_name TEXT NOT NULL,

                email TEXT NOT NULL UNIQUE,

                phone TEXT,

                password TEXT NOT NULL,

                role TEXT NOT NULL DEFAULT 'buyer'
                    CHECK(role IN ('buyer', 'seller', 'admin')),

                avatar TEXT,

                bio TEXT,

                wilaya TEXT,

                municipality TEXT,

                phone_verified INTEGER NOT NULL DEFAULT 0,

                language TEXT NOT NULL DEFAULT 'ar',

                seller_verification_status TEXT
                    NOT NULL DEFAULT 'pending'
                    CHECK(
                        seller_verification_status
                        IN ('pending', 'approved', 'rejected')
                    ),

                seller_activity_type TEXT,

                seller_verification_note TEXT,

                referral_code TEXT UNIQUE,

                referred_by INTEGER,

                is_active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(referred_by)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
            """
        )

        # ====================================================
        # STORES
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL UNIQUE,

                name TEXT NOT NULL,

                description TEXT,

                phone TEXT,

                wilaya TEXT,

                municipality TEXT,

                logo TEXT,

                cover_image TEXT,

                verification_status TEXT
                    NOT NULL DEFAULT 'pending'
                    CHECK(
                        verification_status
                        IN ('pending', 'approved', 'rejected')
                    ),

                verification_note TEXT,

                trust_score REAL NOT NULL DEFAULT 0,

                total_sales INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # PRODUCTS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                store_id INTEGER NOT NULL,

                name TEXT NOT NULL,

                description TEXT,

                price REAL NOT NULL DEFAULT 0,

                discount REAL NOT NULL DEFAULT 0,

                quantity INTEGER NOT NULL DEFAULT 0,

                category TEXT,

                brand TEXT,

                images TEXT,

                video TEXT,

                delivery_wilayas TEXT,

                rating REAL NOT NULL DEFAULT 0,

                reviews_count INTEGER NOT NULL DEFAULT 0,

                views INTEGER NOT NULL DEFAULT 0,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(store_id)
                    REFERENCES stores(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # PRODUCT AVAILABILITY
        #
        # available_now  = ready stock
        # made_to_order  = prepared after order
        # both           = ready stock + made to order
        # ====================================================

        add_column_if_missing(
            connection,
            "products",
            "availability_type",
            "TEXT NOT NULL DEFAULT 'available_now'"
        )

        add_column_if_missing(
            connection,
            "products",
            "preparation_time_minutes",
            "INTEGER NOT NULL DEFAULT 0"
        )

        add_column_if_missing(
            connection,
            "products",
            "colors",
            "TEXT"
        )

        add_column_if_missing(
            connection,
            "products",
            "sizes",
            "TEXT"
        )

        # ====================================================
        # FAVORITES
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, product_id),

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # CART
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                quantity INTEGER NOT NULL DEFAULT 1,

                purchase_mode TEXT NOT NULL DEFAULT 'ready_stock'
                    CHECK(
                        purchase_mode
                        IN ('ready_stock', 'made_to_order')
                    ),

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, product_id, purchase_mode),

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            )
            """
        )

        add_column_if_missing(
            connection,
            "cart_items",
            "purchase_mode",
            "TEXT NOT NULL DEFAULT 'ready_stock'"
        )

        # ====================================================
        # ORDERS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                total_amount REAL NOT NULL DEFAULT 0,

                delivery_address TEXT NOT NULL,

                delivery_wilaya TEXT NOT NULL,

                delivery_phone TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(
                        status IN (
                            'pending',
                            'confirmed',
                            'preparing',
                            'shipped',
                            'in_transit',
                            'delivered',
                            'cancelled',
                            'returned'
                        )
                    ),

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # ORDER ITEMS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                order_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                store_id INTEGER NOT NULL,

                quantity INTEGER NOT NULL,

                price REAL NOT NULL,

                purchase_mode TEXT NOT NULL DEFAULT 'ready_stock'
                    CHECK(
                        purchase_mode
                        IN ('ready_stock', 'made_to_order')
                    ),

                preparation_time_minutes INTEGER NOT NULL DEFAULT 0,

                FOREIGN KEY(order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE RESTRICT,

                FOREIGN KEY(store_id)
                    REFERENCES stores(id)
                    ON DELETE RESTRICT
            )
            """
        )

        add_column_if_missing(
            connection,
            "order_items",
            "purchase_mode",
            "TEXT NOT NULL DEFAULT 'ready_stock'"
        )

        add_column_if_missing(
            connection,
            "order_items",
            "preparation_time_minutes",
            "INTEGER NOT NULL DEFAULT 0"
        )

        # ====================================================
        # REVIEWS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                order_id INTEGER NOT NULL,

                order_item_id INTEGER,

                rating INTEGER NOT NULL
                    CHECK(rating BETWEEN 1 AND 5),

                comment TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, product_id, order_id),

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(order_item_id)
                    REFERENCES order_items(id)
                    ON DELETE SET NULL
            )
            """
        )

        # ====================================================
        # STORE FOLLOWERS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS store_followers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                store_id INTEGER NOT NULL,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, store_id),

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(store_id)
                    REFERENCES stores(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # MESSAGES
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                sender_id INTEGER NOT NULL,

                receiver_id INTEGER NOT NULL,

                product_id INTEGER,

                body TEXT NOT NULL,

                is_read INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(sender_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(receiver_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE SET NULL
            )
            """
        )

        add_column_if_missing(
            connection,
            "messages",
            "product_id",
            "INTEGER"
        )

        # ====================================================
        # NOTIFICATIONS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                title TEXT NOT NULL,

                message TEXT NOT NULL,

                is_read INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # COMPLAINTS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                order_id INTEGER,

                subject TEXT NOT NULL,

                message TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'open'
                    CHECK(
                        status IN (
                            'open',
                            'in_review',
                            'resolved',
                            'closed'
                        )
                    ),

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(order_id)
                    REFERENCES orders(id)
                    ON DELETE SET NULL
            )
            """
        )

        # ====================================================
        # REPORTS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                reporter_id INTEGER NOT NULL,

                reported_user_id INTEGER,

                product_id INTEGER,

                store_id INTEGER,

                reason TEXT NOT NULL,

                details TEXT,

                status TEXT NOT NULL DEFAULT 'open'
                    CHECK(
                        status IN (
                            'open',
                            'in_review',
                            'resolved',
                            'closed'
                        )
                    ),

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(reporter_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(reported_user_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE SET NULL,

                FOREIGN KEY(store_id)
                    REFERENCES stores(id)
                    ON DELETE SET NULL
            )
            """
        )

        # ====================================================
        # BLOCKED USERS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS blocked_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                blocked_user_id INTEGER NOT NULL,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, blocked_user_id),

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(blocked_user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # DISCOUNT CODES
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS discount_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                code TEXT NOT NULL UNIQUE,

                discount_type TEXT NOT NULL DEFAULT 'fixed'
                    CHECK(
                        discount_type IN ('fixed', 'percentage')
                    ),

                value REAL NOT NULL DEFAULT 0,

                max_uses INTEGER,

                used_count INTEGER NOT NULL DEFAULT 0,

                expires_at TEXT,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # REWARD CARDS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reward_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                code TEXT NOT NULL UNIQUE,

                reward_type TEXT NOT NULL,

                reward_value REAL NOT NULL DEFAULT 0,

                used INTEGER NOT NULL DEFAULT 0,

                expires_at TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # REFERRALS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                inviter_id INTEGER NOT NULL,

                invited_user_id INTEGER NOT NULL UNIQUE,

                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(
                        status IN (
                            'pending',
                            'completed',
                            'cancelled'
                        )
                    ),

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                completed_at TEXT,

                FOREIGN KEY(inviter_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(invited_user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # REWARD MILESTONES
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reward_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                milestone_type TEXT NOT NULL,

                milestone_value INTEGER NOT NULL,

                achieved INTEGER NOT NULL DEFAULT 0,

                achieved_at TEXT,

                UNIQUE(user_id, milestone_type, milestone_value),

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # PRICE ALERTS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                target_price REAL NOT NULL,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # PRODUCT VIEWS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                product_id INTEGER NOT NULL,

                user_id INTEGER,

                viewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
            """
        )

        # ====================================================
        # CHAT SETTINGS
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL UNIQUE,

                voice_type TEXT NOT NULL DEFAULT 'female',

                voice_enabled INTEGER NOT NULL DEFAULT 0,

                language TEXT NOT NULL DEFAULT 'ar',

                style TEXT NOT NULL DEFAULT 'friendly',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # INDEXES
        # ====================================================

        indexes = [

            # Users
            """
            CREATE INDEX IF NOT EXISTS
            idx_users_role
            ON users(role)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_users_verification
            ON users(seller_verification_status)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_users_wilaya
            ON users(wilaya)
            """,

            # Stores
            """
            CREATE INDEX IF NOT EXISTS
            idx_stores_verification
            ON stores(verification_status)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_stores_wilaya
            ON stores(wilaya)
            """,

            # Products
            """
            CREATE INDEX IF NOT EXISTS
            idx_products_store
            ON products(store_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_products_category
            ON products(category)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_products_active
            ON products(active)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_products_availability
            ON products(availability_type)
            """,

            # Favorites
            """
            CREATE INDEX IF NOT EXISTS
            idx_favorites_user
            ON favorites(user_id)
            """,

            # Cart
            """
            CREATE INDEX IF NOT EXISTS
            idx_cart_user
            ON cart_items(user_id)
            """,

            # Orders
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_user
            ON orders(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_status
            ON orders(status)
            """,

            # Order items
            """
            CREATE INDEX IF NOT EXISTS
            idx_order_items_order
            ON order_items(order_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_order_items_product
            ON order_items(product_id)
            """,

            # Reviews
            """
            CREATE INDEX IF NOT EXISTS
            idx_reviews_product
            ON reviews(product_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_reviews_user
            ON reviews(user_id)
            """,

            # Followers
            """
            CREATE INDEX IF NOT EXISTS
            idx_followers_store
            ON store_followers(store_id)
            """,

            # Messages
            """
            CREATE INDEX IF NOT EXISTS
            idx_messages_sender
            ON messages(sender_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_messages_receiver
            ON messages(receiver_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_messages_product
            ON messages(product_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_messages_conversation
            ON messages(sender_id, receiver_id, created_at)
            """,

            # Notifications
            """
            CREATE INDEX IF NOT EXISTS
            idx_notifications_user
            ON notifications(user_id)
            """,

            # Complaints
            """
            CREATE INDEX IF NOT EXISTS
            idx_complaints_status
            ON complaints(status)
            """,

            # Reports
            """
            CREATE INDEX IF NOT EXISTS
            idx_reports_status
            ON reports(status)
            """,

            # Rewards
            """
            CREATE INDEX IF NOT EXISTS
            idx_reward_cards_user
            ON reward_cards(user_id)
            """,

            # Referrals
            """
            CREATE INDEX IF NOT EXISTS
            idx_referrals_inviter
            ON referrals(inviter_id)
            """,

            # Price alerts
            """
            CREATE INDEX IF NOT EXISTS
            idx_price_alerts_product
            ON price_alerts(product_id)
            """,

            # Product views
            """
            CREATE INDEX IF NOT EXISTS
            idx_product_views_product
            ON product_views(product_id)
            """,

            # Store followers
            """
            CREATE INDEX IF NOT EXISTS
            idx_store_followers_user
            ON store_followers(user_id)
            """
        ]

        for index_sql in indexes:
            connection.execute(index_sql)

        # ====================================================
        # MIGRATE OLD COLUMNS / DATA
        # ====================================================

        # Old installations may not have is_active.
        add_column_if_missing(
            connection,
            "users",
            "is_active",
            "INTEGER NOT NULL DEFAULT 1"
        )

        # Old notifications might have had different structures.
        # We keep the canonical column name: message.

        # Old complaints also use message as canonical column.
        # This matches models.py.

        # ====================================================
        # ADMIN ACCOUNT
        # ====================================================

        admin_email = os.getenv(
            "DZMARKET_ADMIN_EMAIL",
            "admin@dzmarket.local"
        )

        admin_password = os.getenv(
            "DZMARKET_ADMIN_PASSWORD"
        )

        admin = connection.execute(
            """
            SELECT id
            FROM users
            WHERE role = 'admin'
            LIMIT 1
            """
        ).fetchone()

        if not admin and admin_password:

            connection.execute(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    password,
                    role,
                    referral_code,
                    is_active
                )
                VALUES (?, ?, ?, 'admin', ?, 1)
                """,
                (
                    "DZ MARKET Admin",
                    admin_email,
                    generate_password_hash(admin_password),
                    generate_code("ADMIN")
                )
            )

        # ====================================================
        # COMMIT
        # ====================================================

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":
    init_database()
    print("DZ MARKET database initialized successfully.")
    print(f"Database: {DATABASE_PATH}")
