import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "dzmarket.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def add_column_if_missing(connection, table, column, definition):
    columns = connection.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    existing_columns = {column["name"] for column in columns}

    if column not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def init_database():
    connection = get_connection()

    connection.executescript("""
        =========================================================
        USERS
        =========================================================
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


        =========================================================
        STORES
        =========================================================
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

            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );


        =========================================================
        PRODUCTS
        =========================================================
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

            FOREIGN KEY (store_id) REFERENCES stores(id)
                ON DELETE CASCADE
        );


        =========================================================
        FAVORITES
        =========================================================
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, product_id),

            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        );


        =========================================================
        CART
        =========================================================
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, product_id),

            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        );


        =========================================================
        ORDERS
        =========================================================
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            total REAL NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'pending',

            delivery_address TEXT DEFAULT '',
            delivery_wilaya TEXT DEFAULT '',
            delivery_municipality TEXT DEFAULT '',
            delivery_phone TEXT DEFAULT '',

            buyer_confirmed INTEGER NOT NULL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );


        =========================================================
        ORDER ITEMS
        =========================================================
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            store_id INTEGER,

            quantity INTEGER NOT NULL DEFAULT 1,
            price REAL NOT NULL DEFAULT 0,

            FOREIGN KEY (order_id) REFERENCES orders(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id) REFERENCES products(id),

            FOREIGN KEY (store_id) REFERENCES stores(id)
        );


        =========================================================
        REVIEWS
        =========================================================
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

            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE,

            FOREIGN KEY (order_id) REFERENCES orders(id)
                ON DELETE CASCADE,

            FOREIGN KEY (order_item_id) REFERENCES order_items(id)
        );


        =========================================================
        STORE FOLLOWS
        =========================================================
        CREATE TABLE IF NOT EXISTS store_followers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, store_id),

            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (store_id) REFERENCES stores(id)
                ON DELETE CASCADE
        );


        =========================================================
        BLOCKED USERS
        =========================================================
        CREATE TABLE IF NOT EXISTS blocked_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            blocker_id INTEGER NOT NULL,
            blocked_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(blocker_id, blocked_id),

            FOREIGN KEY (blocker_id) REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (blocked_id) REFERENCES users(id)
                ON DELETE CASCADE
        );


        =========================================================
        REPORTS
        =========================================================
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            target_type TEXT NOT NULL,
            target_id INTEGER,

            reason TEXT NOT NULL,
            message TEXT DEFAULT '',

            status TEXT NOT NULL DEFAULT 'open',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );


        =========================================================
        COMPLAINTS
        =========================================================
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            order_id INTEGER,

            subject TEXT NOT NULL,
            message TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'open',

            created_at TIMESTAMP DEFAULT CURRENT         CREATE TABLE IF NOT EXISTS chat_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            voice_type TEXT NOT NULL DEFAULT 'female',
            voice_enabled INTEGER NOT NULL DEFAULT 1,
            language TEXT NOT NULL DEFAULT 'ar',
            style TEXT NOT NULL DEFAULT 'friendly',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
