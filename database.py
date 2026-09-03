import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "dzmarket.db"


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def add_column_if_missing(
    connection,
    table,
    column,
    definition
):
    columns = connection.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    existing = {
        column_info["name"]
        for column_info in columns
    }

    if column not in existing:
        connection.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def init_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'buyer',
            avatar TEXT,
            bio TEXT,
            wilaya TEXT,
            municipality TEXT,
            phone_verified INTEGER DEFAULT 0,
            seller_verification_status TEXT DEFAULT 'none',
            seller_activity_type TEXT,
            seller_verification_note TEXT,
            language TEXT DEFAULT 'ar',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            phone TEXT,
            wilaya TEXT,
            municipality TEXT,
            logo TEXT,
            cover_image TEXT,
            verification_status TEXT DEFAULT 'pending',
            trust_score REAL DEFAULT 0,
            total_sales INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            price REAL NOT NULL DEFAULT 0,
            discount REAL DEFAULT 0,
            quantity INTEGER DEFAULT 0,
            category TEXT,
            brand TEXT,
            images TEXT,
            video TEXT,
            delivery_wilayas TEXT,
            rating REAL DEFAULT 0,
            reviews_count INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(store_id) REFERENCES stores(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, product_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, product_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0,
            delivery_address TEXT,
            delivery_wilaya TEXT,
            delivery_phone TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            store_id INTEGER,
            quantity INTEGER NOT NULL DEFAULT 1,
            price REAL NOT NULL DEFAULT 0,
            FOREIGN KEY(order_id) REFERENCES orders(id)
                ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id)
                ON DELETE CASCADE,
            FOREIGN KEY(store_id) REFERENCES stores(id)
                ON DELETE SET NULL
        );

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
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id)
                ON DELETE CASCADE,
            FOREIGN KEY(order_id) REFERENCES orders(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS store_followers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, store_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE,
            FOREIGN KEY(store_id) REFERENCES stores(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sender_id) REFERENCES users(id)
                ON DELETE CASCADE,
            FOREIGN KEY(receiver_id) REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER,
            subject TEXT,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            message TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS blocked_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blocker_id INTEGER NOT NULL,
            blocked_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(blocker_id, blocked_id),
            FOREIGN KEY(blocker_id) REFERENCES users(id)
                ON DELETE CASCADE,
            FOREIGN KEY(blocked_id) REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS discount_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER,
            code TEXT UNIQUE NOT NULL,
            discount_percent REAL DEFAULT 0,
            max_uses INTEGER DEFAULT 0,
            used_count INTEGER DEFAULT 0,
            expires_at TEXT,
            active INTEGER DEFAULT 1,
            FOREIGN KEY(store_id) REFERENCES stores(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            target_price REAL NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, product_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS product_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE SET NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chat_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            voice_type TEXT DEFAULT 'female',
            voice_enabled INTEGER DEFAULT 0,
            language TEXT DEFAULT 'ar',
            style TEXT DEFAULT 'friendly',
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );
        """
    )

    # --------------------------------------------------------
    # MIGRATIONS FOR EXISTING DATABASES
    # --------------------------------------------------------

    add_column_if_missing(
        connection,
        "users",
        "phone",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "users",
        "avatar",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "users",
        "bio",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "users",
        "wilaya",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "users",
        "municipality",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "users",
        "phone_verified",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "users",
        "seller_verification_status",
        "TEXT DEFAULT 'none'"
    )

    add_column_if_missing(
        connection,
        "users",
        "seller_activity_type",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "users",
        "seller_verification_note",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "users",
        "language",
        "TEXT DEFAULT 'ar'"
    )

    add_column_if_missing(
        connection,
        "stores",
        "municipality",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "stores",
        "logo",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "stores",
        "cover_image",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "stores",
        "verification_status",
        "TEXT DEFAULT 'pending'"
    )

    add_column_if_missing(
        connection,
        "stores",
        "trust_score",
        "REAL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "stores",
        "total_sales",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "orders",
        "total_amount",
        "REAL DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "orders",
        "delivery_phone",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "orders",
        "delivery_wilaya",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "orders",
        "status",
        "TEXT DEFAULT 'pending'"
    )

    add_column_if_missing(
        connection,
        "discount_codes",
        "max_uses",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "discount_codes",
        "used_count",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        connection,
        "reports",
        "message",
        "TEXT DEFAULT ''"
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_database()
    print("DZ MARKET database initialized successfully.")
