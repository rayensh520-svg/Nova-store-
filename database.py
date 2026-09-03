import sqlite3
from pathlib import Path


# ============================================================
# DZ MARKET 🇩🇿
# DATABASE CONFIGURATION
# ============================================================

DATABASE_PATH = Path(__file__).resolve().parent / "dzmarket.db"


def get_connection():
    """
    فتح اتصال بقاعدة البيانات.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def add_column_if_missing(connection, table, column, definition):
    """
    إضافة عمود إذا لم يكن موجودًا.
    مفيد عند تحديث قاعدة بيانات قديمة.
    """
    columns = connection.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    existing_columns = {
        column_info["name"]
        for column_info in columns
    }

    if column not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def init_database():
    """
    إنشاء قاعدة بيانات DZ MARKET وجميع الجداول الأساسية.
    """

    connection = get_connection()

    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        -- ====================================================
        -- USERS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL DEFAULT 'buyer',

            phone TEXT DEFAULT '',

            profile_image TEXT DEFAULT '',

            phone_verified INTEGER NOT NULL DEFAULT 0,

            language TEXT NOT NULL DEFAULT 'ar',

            dark_mode INTEGER NOT NULL DEFAULT 0,

            notifications_enabled INTEGER NOT NULL DEFAULT 1,

            seller_verification_status TEXT NOT NULL DEFAULT 'none',

            seller_activity_type TEXT DEFAULT '',

            seller_verification_note TEXT DEFAULT '',

            seller_verified_at TIMESTAMP,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );


        -- ====================================================
        -- STORES
        -- ====================================================

        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL UNIQUE,

            name TEXT NOT NULL,

            description TEXT DEFAULT '',

            phone TEXT DEFAULT '',

            wilaya TEXT DEFAULT '',

            municipality TEXT DEFAULT '',

            logo TEXT DEFAULT '',

            cover_image TEXT DEFAULT '',

            opening_hours TEXT DEFAULT '',

            followers_count INTEGER NOT NULL DEFAULT 0,

            sales_count INTEGER NOT NULL DEFAULT 0,

            trust_score REAL NOT NULL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- PRODUCTS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            store_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            description TEXT DEFAULT '',

            brand_name TEXT DEFAULT '',

            brand_logo TEXT DEFAULT '',

            price REAL NOT NULL DEFAULT 0,

            old_price REAL DEFAULT 0,

            discount_percent REAL NOT NULL DEFAULT 0,

            quantity INTEGER NOT NULL DEFAULT 0,

            category TEXT DEFAULT '',

            image TEXT DEFAULT '',

            video TEXT DEFAULT '',

            is_algerian INTEGER NOT NULL DEFAULT 0,

            delivery_wilayas TEXT DEFAULT '',

            rating REAL NOT NULL DEFAULT 0,

            reviews_count INTEGER NOT NULL DEFAULT 0,

            is_active INTEGER NOT NULL DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (store_id)
                REFERENCES stores(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- FAVORITES
        -- ====================================================

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, product_id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- CART
        -- ====================================================

        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, product_id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- ORDERS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            total_amount REAL NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'pending',

            delivery_address TEXT DEFAULT '',

            delivery_wilaya TEXT DEFAULT '',

            delivery_municipality TEXT DEFAULT '',

            delivery_phone TEXT DEFAULT '',

            buyer_confirmed INTEGER NOT NULL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- ORDER ITEMS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            store_id INTEGER,

            quantity INTEGER NOT NULL DEFAULT 1,

            price REAL NOT NULL DEFAULT 0,

            FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(id),

            FOREIGN KEY (store_id)
                REFERENCES stores(id)
        );


        -- ====================================================
        -- REVIEWS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            order_id INTEGER NOT NULL,

            order_item_id INTEGER,

            rating INTEGER NOT NULL,

            comment TEXT DEFAULT '',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, product_id, order_id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
                ON DELETE CASCADE,

            FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE,

            FOREIGN KEY (order_item_id)
                REFERENCES order_items(id)
        );


        -- ====================================================
        -- STORE FOLLOWERS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS store_followers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            store_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, store_id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (store_id)
                REFERENCES stores(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- BLOCKED USERS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS blocked_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            blocker_id INTEGER NOT NULL,

            blocked_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(blocker_id, blocked_id),

            FOREIGN KEY (blocker_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (blocked_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- REPORTS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            target_type TEXT NOT NULL,

            target_id INTEGER,

            reason TEXT NOT NULL,

            message TEXT DEFAULT '',

            status TEXT NOT NULL DEFAULT 'open',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- COMPLAINTS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            order_id INTEGER,

            subject TEXT NOT NULL,

            message TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'open',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE SET NULL
        );


        -- ====================================================
        -- MESSAGES
        -- ====================================================

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            sender_id INTEGER NOT NULL,

            receiver_id INTEGER NOT NULL,

            body TEXT NOT NULL,

            is_read INTEGER NOT NULL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (sender_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (receiver_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- CHAT SETTINGS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS chat_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL UNIQUE,

            voice_type TEXT NOT NULL DEFAULT 'female',

            voice_enabled INTEGER NOT NULL DEFAULT 1,

            language TEXT NOT NULL DEFAULT 'ar',

            style TEXT NOT NULL DEFAULT 'friendly',

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- NOTIFICATIONS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            message TEXT NOT NULL,

            is_read INTEGER NOT NULL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- DISCOUNT CODES
        -- ====================================================

        CREATE TABLE IF NOT EXISTS discount_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            store_id INTEGER,

            code TEXT NOT NULL UNIQUE,

            discount_percent REAL NOT NULL DEFAULT 0,

            max_uses INTEGER DEFAULT 0,

            used_count INTEGER NOT NULL DEFAULT 0,

            expires_at TIMESTAMP,

            is_active INTEGER NOT NULL DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (store_id)
                REFERENCES stores(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- PRICE ALERTS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            target_price REAL NOT NULL,

            is_active INTEGER NOT NULL DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, product_id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
                ON DELETE CASCADE
        );


        -- ====================================================
        -- PRODUCT VIEWS
        -- ====================================================

        CREATE TABLE IF NOT EXISTS product_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id INTEGER NOT NULL,

            user_id INTEGER,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
                ON DELETE CASCADE,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
        );


        -- ====================================================
        -- INDEXES
        -- ====================================================

        CREATE INDEX IF NOT EXISTS idx_products_store
        ON products(store_id);

        CREATE INDEX IF NOT EXISTS idx_products_category
        ON products(category);

        CREATE INDEX IF NOT EXISTS idx_messages_sender
        ON messages(sender_id);

        CREATE INDEX IF NOT EXISTS idx_messages_receiver
        ON messages(receiver_id);

        CREATE INDEX IF NOT EXISTS idx_notifications_user
        ON notifications(user_id);

        CREATE INDEX IF NOT EXISTS idx_orders_user
        ON orders(user_id);

        CREATE INDEX IF NOT EXISTS idx_reviews_product
        ON reviews(product_id);

        CREATE INDEX IF NOT EXISTS idx_product_views_product
        ON product_views(product_id);

        CREATE INDEX IF NOT EXISTS idx_store_followers_store
        ON store_followers(store_id);
        """
    )


    # ========================================================
    # MIGRATION
    # ========================================================
    # إذا كانت عندك قاعدة بيانات قديمة، نحاول نضيف الأعمدة
    # الجديدة بدون حذف البيانات الموجودة.

    add_column_if_missing(
        connection,
        "users",
        "phone",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "users",
        "profile_image",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "users",
        "phone_verified",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "users",
        "language",
        "TEXT NOT NULL DEFAULT 'ar'"
    )

    add_column_if_missing(
        connection,
        "users",
        "dark_mode",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "users",
        "notifications_enabled",
        "INTEGER NOT NULL DEFAULT 1"
    )

    add_column_if_missing(
        connection,
        "users",
        "seller_verification_status",
        "TEXT NOT NULL DEFAULT 'none'"
    )

    add_column_if_missing(
        connection,
        "users",
        "seller_activity_type",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "users",
        "seller_verification_note",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "users",
        "seller_verified_at",
        "TIMESTAMP"
    )


    # STORES

    add_column_if_missing(
        connection,
        "stores",
        "municipality",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "stores",
        "logo",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "stores",
        "cover_image",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "stores",
        "opening_hours",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "stores",
        "followers_count",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "stores",
        "sales_count",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "stores",
        "trust_score",
        "REAL NOT NULL DEFAULT 0"
    )


    # PRODUCTS

    add_column_if_missing(
        connection,
        "products",
        "brand_name",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "products",
        "brand_logo",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "products",
        "old_price",
        "REAL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "products",
        "discount_percent",
        "REAL NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "products",
        "video",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "products",
        "is_algerian",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "products",
        "delivery_wilayas",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "products",
        "rating",
        "REAL NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "products",
        "reviews_count",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "products",
        "is_active",
        "INTEGER NOT NULL DEFAULT 1"
    )


    # ORDERS

    add_column_if_missing(
        connection,
        "orders",
        "total_amount",
        "REAL NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "orders",
        "delivery_wilaya",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "orders",
        "delivery_municipality",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "orders",
        "delivery_phone",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        connection,
        "orders",
        "buyer_confirmed",
        "INTEGER NOT NULL DEFAULT 0"
    )


    connection.commit()
    connection.close()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    init_database()
    print("DZ MARKET database initialized successfully. 🇩🇿")
