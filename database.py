import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash


# =========================================================
# DATABASE CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "dzmarket.db"


# =========================================================
# CONNECTION
# =========================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    connection = get_connection()

    try:

        # =================================================
        # USERS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                full_name TEXT NOT NULL,

                email TEXT NOT NULL UNIQUE,

                phone TEXT DEFAULT '',

                password TEXT NOT NULL,

                role TEXT NOT NULL DEFAULT 'buyer'
                    CHECK (
                        role IN (
                            'buyer',
                            'seller',
                            'admin'
                        )
                    ),

                avatar TEXT DEFAULT '',

                bio TEXT DEFAULT '',

                wilaya TEXT DEFAULT '',

                municipality TEXT DEFAULT '',

                phone_verified INTEGER DEFAULT 0,

                language TEXT DEFAULT 'ar',

                seller_verification_status
                    TEXT DEFAULT 'pending',

                seller_activity_type
                    TEXT DEFAULT '',

                seller_verification_note
                    TEXT DEFAULT '',

                referral_code TEXT UNIQUE,

                referred_by INTEGER,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    referred_by
                )
                REFERENCES users(id)
                ON DELETE SET NULL
            )
            """
        )


        # =================================================
        # STORES
        # =================================================

        connection.execute(
            """
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

                verification_status
                    TEXT DEFAULT 'pending',

                trust_score REAL DEFAULT 0,

                total_sales INTEGER DEFAULT 0,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # PRODUCTS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                store_id INTEGER NOT NULL,

                name TEXT NOT NULL,

                description TEXT DEFAULT '',

                price REAL NOT NULL DEFAULT 0,

                discount REAL DEFAULT 0,

                quantity INTEGER DEFAULT 0,

                category TEXT DEFAULT '',

                brand TEXT DEFAULT '',

                images TEXT DEFAULT '',

                video TEXT DEFAULT '',

                delivery_wilayas TEXT DEFAULT '',

                rating REAL DEFAULT 0,

                reviews_count INTEGER DEFAULT 0,

                views INTEGER DEFAULT 0,

                active INTEGER DEFAULT 1,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    store_id
                )
                REFERENCES stores(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # FAVORITES
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    user_id,
                    product_id
                ),

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    product_id
                )
                REFERENCES products(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # CART
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                quantity INTEGER NOT NULL DEFAULT 1,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    user_id,
                    product_id
                ),

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    product_id
                )
                REFERENCES products(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # ORDERS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                total_amount REAL DEFAULT 0,

                delivery_address TEXT DEFAULT '',

                delivery_wilaya TEXT DEFAULT '',

                delivery_phone TEXT DEFAULT '',

                status TEXT DEFAULT 'pending',

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # ORDER ITEMS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                order_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                store_id INTEGER,

                quantity INTEGER NOT NULL DEFAULT 1,

                price REAL NOT NULL DEFAULT 0,

                FOREIGN KEY (
                    order_id
                )
                REFERENCES orders(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    product_id
                )
                REFERENCES products(id),

                FOREIGN KEY (
                    store_id
                )
                REFERENCES stores(id)
                ON DELETE SET NULL
            )
            """
        )


        # =================================================
        # REVIEWS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                order_id INTEGER,

                order_item_id INTEGER,

                rating INTEGER NOT NULL,

                comment TEXT DEFAULT '',

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    user_id,
                    product_id,
                    order_id
                ),

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    product_id
                )
                REFERENCES products(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    order_id
                )
                REFERENCES orders(id)
                ON DELETE SET NULL
            )
            """
        )


        # =================================================
        # STORE FOLLOWERS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS store_followers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                store_id INTEGER NOT NULL,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    user_id,
                    store_id
                ),

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    store_id
                )
                REFERENCES stores(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # MESSAGES
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                sender_id INTEGER NOT NULL,

                receiver_id INTEGER NOT NULL,

                body TEXT NOT NULL,

                is_read INTEGER DEFAULT 0,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    sender_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    receiver_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # NOTIFICATIONS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                title TEXT NOT NULL,

                message TEXT NOT NULL,

                is_read INTEGER DEFAULT 0,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # COMPLAINTS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                order_id INTEGER,

                subject TEXT DEFAULT '',

                message TEXT NOT NULL,

                status TEXT DEFAULT 'open',

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    order_id
                )
                REFERENCES orders(id)
                ON DELETE SET NULL
            )
            """
        )


        # =================================================
        # REPORTS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                target_type TEXT NOT NULL,

                target_id INTEGER NOT NULL,

                reason TEXT NOT NULL,

                message TEXT DEFAULT '',

                status TEXT DEFAULT 'open',

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # BLOCKED USERS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS blocked_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                blocker_id INTEGER NOT NULL,

                blocked_id INTEGER NOT NULL,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    blocker_id,
                    blocked_id
                ),

                FOREIGN KEY (
                    blocker_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    blocked_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # DISCOUNT CODES
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS discount_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                store_id INTEGER NOT NULL,

                code TEXT NOT NULL UNIQUE,

                discount_percent REAL DEFAULT 0,

                max_uses INTEGER DEFAULT 0,

                used_count INTEGER DEFAULT 0,

                expires_at TEXT,

                active INTEGER DEFAULT 1,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    store_id
                )
                REFERENCES stores(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # REWARD CARDS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reward_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                code TEXT NOT NULL UNIQUE,

                title TEXT NOT NULL,

                description TEXT DEFAULT '',

                discount_percent REAL DEFAULT 0,

                reward_type TEXT DEFAULT 'discount',

                source TEXT DEFAULT 'order',

                expires_at TEXT,

                used INTEGER DEFAULT 0,

                active INTEGER DEFAULT 1,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # REFERRALS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                inviter_id INTEGER NOT NULL,

                invited_user_id INTEGER NOT NULL UNIQUE,

                referral_code TEXT NOT NULL,

                status TEXT DEFAULT 'registered',

                reward_granted INTEGER DEFAULT 0,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                completed_at TIMESTAMP,

                FOREIGN KEY (
                    inviter_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    invited_user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # REWARD MILESTONES
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reward_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                milestone INTEGER NOT NULL,

                reward_card_id INTEGER,

                achieved_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    user_id,
                    milestone
                ),

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    reward_card_id
                )
                REFERENCES reward_cards(id)
                ON DELETE SET NULL
            )
            """
        )


        # =================================================
        # PRICE ALERTS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                target_price REAL NOT NULL,

                active INTEGER DEFAULT 1,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    user_id,
                    product_id
                ),

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    product_id
                )
                REFERENCES products(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # PRODUCT VIEWS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER,

                product_id INTEGER NOT NULL,

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE SET NULL,

                FOREIGN KEY (
                    product_id
                )
                REFERENCES products(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # CHAT SETTINGS
        # =================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL UNIQUE,

                voice_type TEXT DEFAULT 'female',

                voice_enabled INTEGER DEFAULT 0,

                language TEXT DEFAULT 'ar',

                style TEXT DEFAULT 'friendly',

                created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )


        # =================================================
        # INDEXES
        # =================================================

        indexes = [

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
            idx_orders_user
            ON orders(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_status
            ON orders(status)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_messages_receiver
            ON messages(receiver_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_notifications_user
            ON notifications(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_reward_cards_user
            ON reward_cards(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_referrals_inviter
            ON referrals(inviter_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_product_views_product
            ON product_views(product_id)
            """
        ]


        for index_sql in indexes:
            connection.execute(index_sql)


        # =================================================
        # DEFAULT ADMIN
        # =================================================

        admin = connection.execute(
            """
            SELECT id
            FROM users
            WHERE role = 'admin'
            LIMIT 1
            """
        ).fetchone()


        if not admin:

            connection.execute(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    password,
                    role,
                    referral_code
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "DZ MARKET Admin",
                    "admin@dzmarket.local",
                    generate_password_hash(
                        "ChangeMe123!"
                    ),
                    "admin",
                    generate_code("ADMIN")
                )
            )


        # =================================================
        # MIGRATIONS
        # =================================================

        migrations = [

            (
                "users",
                "referral_code",
                "TEXT UNIQUE"
            ),

            (
                "users",
                "referred_by",
                "INTEGER"
            ),

            (
                "users",
                "avatar",
                "TEXT DEFAULT ''"
            ),

            (
                "users",
                "bio",
                "TEXT DEFAULT ''"
            ),

            (
                "users",
                "wilaya",
                "TEXT DEFAULT ''"
            ),

            (
                "users",
                "municipality",
                "TEXT DEFAULT ''"
            ),

            (
                "users",
                "phone_verified",
                "INTEGER DEFAULT 0"
            ),

            (
                "users",
                "language",
                "TEXT DEFAULT 'ar'"
            ),

            (
                "orders",
                "total_amount",
                "REAL DEFAULT 0"
            ),

            (
                "orders",
                "delivery_address",
                "TEXT DEFAULT ''"
            ),

            (
                "orders",
                "delivery_wilaya",
                "TEXT DEFAULT ''"
            ),

            (
                "orders",
                "delivery_phone",
                "TEXT DEFAULT ''"
            ),

            (
                "orders",
                "updated_at",
                "TIMESTAMP"
            ),

            (
                "products",
                "views",
                "INTEGER DEFAULT 0"
            ),

            (
                "products",
                "video",
                "TEXT DEFAULT ''"
            ),

            (
                "stores",
                "trust_score",
                "REAL DEFAULT 0"
            ),

            (
                "stores",
                "total_sales",
                "INTEGER DEFAULT 0"
            )
        ]


        for table, column, definition in migrations:

            columns = connection.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()

            existing = {
                row["name"]
                for row in columns
            }

            if column not in existing:

                try:

                    connection.execute(
                        f"""
                        ALTER TABLE {table}
                        ADD COLUMN {column}
                        {definition}
                        """
                    )

                except sqlite3.OperationalError:
                    pass


        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# =========================================================
# AUTO INIT
# =========================================================

if __name__ == "__main__":
    init_database()
    print("DZ MARKET database initialized successfully.")
