import sqlite3
from pathlib import Path


# ==========================================================
# VYORA DATABASE
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "vyora.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():
    """
    فتح اتصال بقاعدة البيانات.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def init_db():

    db = get_db()

    try:

        # --------------------------------------------------
        # USERS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                full_name TEXT NOT NULL,

                email TEXT NOT NULL UNIQUE,

                password_hash TEXT NOT NULL,

                account_type TEXT NOT NULL
                    CHECK (
                        account_type IN ('buyer', 'seller')
                    ),

                is_active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


        # --------------------------------------------------
        # SELLERS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS sellers (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL UNIQUE,

                approval_status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (
                        approval_status IN (
                            'pending',
                            'approved',
                            'rejected'
                        )
                    ),

                phone TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # STORES
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS stores (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                seller_id INTEGER NOT NULL UNIQUE,

                store_name TEXT NOT NULL,

                description TEXT,

                category TEXT,

                location TEXT,

                phone TEXT,

                opening_hours TEXT,

                delivery_info TEXT,

                is_visible INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (seller_id)
                    REFERENCES sellers(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # PRODUCTS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS products (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                store_id INTEGER NOT NULL,

                name TEXT NOT NULL,

                description TEXT,

                category TEXT,

                price REAL NOT NULL DEFAULT 0,

                currency TEXT NOT NULL DEFAULT 'DZD',

                availability_mode TEXT NOT NULL DEFAULT 'in_stock'
                    CHECK (
                        availability_mode IN (
                            'in_stock',
                            'made_to_order'
                        )
                    ),

                quantity INTEGER,

                delivery_info TEXT,

                is_visible INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (store_id)
                    REFERENCES stores(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # PRODUCT MEDIA
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS product_media (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                product_id INTEGER NOT NULL,

                media_type TEXT NOT NULL
                    CHECK (
                        media_type IN ('image', 'video')
                    ),

                file_path TEXT NOT NULL,

                sort_order INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # PRODUCT VARIANTS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS product_variants (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                product_id INTEGER NOT NULL,

                variant_name TEXT NOT NULL,

                variant_value TEXT NOT NULL,

                additional_price REAL NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # CARTS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS carts (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL UNIQUE,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # CART ITEMS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                cart_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                quantity INTEGER NOT NULL
                    CHECK (quantity > 0),

                variant_id INTEGER,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(cart_id, product_id, variant_id),

                FOREIGN KEY (cart_id)
                    REFERENCES carts(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (variant_id)
                    REFERENCES product_variants(id)
                    ON DELETE SET NULL
            )
        """)


        # --------------------------------------------------
        # ORDERS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS orders (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                order_number TEXT NOT NULL UNIQUE,

                buyer_id INTEGER NOT NULL,

                store_id INTEGER NOT NULL,

                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (
                        status IN (
                            'pending',
                            'confirmed',
                            'preparing',
                            'ready',
                            'shipping',
                            'delivered',
                            'cancelled',
                            'returned',
                            'complaint'
                        )
                    ),

                payment_method TEXT NOT NULL DEFAULT 'cash_on_delivery',

                payment_status TEXT NOT NULL DEFAULT 'pending',

                subtotal REAL NOT NULL DEFAULT 0,

                delivery_fee REAL NOT NULL DEFAULT 0,

                total REAL NOT NULL DEFAULT 0,

                delivery_name TEXT NOT NULL,

                delivery_phone TEXT NOT NULL,

                delivery_wilaya TEXT NOT NULL,

                delivery_city TEXT,

                delivery_address TEXT NOT NULL,

                delivery_note TEXT,

                order_note TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (buyer_id)
                    REFERENCES users(id),

                FOREIGN KEY (store_id)
                    REFERENCES stores(id)
            )
        """)


        # --------------------------------------------------
        # ORDER ITEMS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                order_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                product_name_snapshot TEXT NOT NULL,

                unit_price REAL NOT NULL,

                quantity INTEGER NOT NULL
                    CHECK (quantity > 0),

                variant_snapshot TEXT,

                subtotal REAL NOT NULL,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (product_id)
                    REFERENCES products(id)
            )
        """)


        # --------------------------------------------------
        # ORDER STATUS HISTORY
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS order_status_history (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                order_id INTEGER NOT NULL,

                status TEXT NOT NULL,

                note TEXT,

                changed_by INTEGER,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (changed_by)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
        """)


        # --------------------------------------------------
        # FAVORITES
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, product_id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # MESSAGES
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                sender_id INTEGER NOT NULL,

                receiver_id INTEGER NOT NULL,

                order_id INTEGER,

                product_id INTEGER,

                message_type TEXT NOT NULL DEFAULT 'text'
                    CHECK (
                        message_type IN (
                            'text',
                            'image',
                            'video',
                            'audio'
                        )
                    ),

                content TEXT,

                file_path TEXT,

                is_read INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (sender_id)
                    REFERENCES users(id),

                FOREIGN KEY (receiver_id)
                    REFERENCES users(id),

                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE SET NULL,

                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE SET NULL
            )
        """)


        # --------------------------------------------------
        # NOTIFICATIONS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                title TEXT NOT NULL,

                message TEXT NOT NULL,

                notification_type TEXT,

                reference_id INTEGER,

                is_read INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # REVIEWS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                order_id INTEGER NOT NULL,

                product_id INTEGER NOT NULL,

                buyer_id INTEGER NOT NULL,

                rating INTEGER NOT NULL
                    CHECK (rating >= 1 AND rating <= 5),

                comment TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(order_id, product_id),

                FOREIGN KEY (order_id)
                    REFERENCES orders(id),

                FOREIGN KEY (product_id)
                    REFERENCES products(id),

                FOREIGN KEY (buyer_id)
                    REFERENCES users(id)
            )
        """)


        # --------------------------------------------------
        # REVIEW MEDIA
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS review_media (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                review_id INTEGER NOT NULL,

                file_path TEXT NOT NULL,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (review_id)
                    REFERENCES reviews(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # COMPLAINTS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS complaints (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                order_id INTEGER NOT NULL,

                user_id INTEGER NOT NULL,

                reason TEXT NOT NULL,

                description TEXT,

                status TEXT NOT NULL DEFAULT 'open'
                    CHECK (
                        status IN (
                            'open',
                            'under_review',
                            'resolved',
                            'rejected'
                        )
                    ),

                resolution TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (order_id)
                    REFERENCES orders(id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            )
        """)


        # --------------------------------------------------
        # SELLER TRUST
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS seller_trust (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                seller_id INTEGER NOT NULL UNIQUE,

                fulfillment_rate REAL NOT NULL DEFAULT 0,

                cancellation_rate REAL NOT NULL DEFAULT 0,

                return_rate REAL NOT NULL DEFAULT 0,

                complaint_rate REAL NOT NULL DEFAULT 0,

                rating REAL NOT NULL DEFAULT 0,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (seller_id)
                    REFERENCES sellers(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # FINANCIAL TRANSACTIONS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS financial_transactions (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                seller_id INTEGER NOT NULL,

                order_id INTEGER,

                transaction_type TEXT NOT NULL,

                gross_amount REAL NOT NULL DEFAULT 0,

                commission_amount REAL NOT NULL DEFAULT 0,

                delivery_amount REAL NOT NULL DEFAULT 0,

                other_amount REAL NOT NULL DEFAULT 0,

                net_amount REAL NOT NULL DEFAULT 0,

                status TEXT NOT NULL DEFAULT 'pending',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (seller_id)
                    REFERENCES sellers(id),

                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE SET NULL
            )
        """)


        # --------------------------------------------------
        # PREMIUM SUBSCRIPTIONS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS premium_subscriptions (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                seller_id INTEGER NOT NULL,

                status TEXT NOT NULL DEFAULT 'inactive',

                started_at TEXT,

                expires_at TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (seller_id)
                    REFERENCES sellers(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # AUDIT LOGS
        # --------------------------------------------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER,

                action TEXT NOT NULL,

                entity_type TEXT,

                entity_id INTEGER,

                details TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
        """)


        # --------------------------------------------------
        # INDEXES
        # --------------------------------------------------

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_store
            ON products(store_id)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_category
            ON products(category)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_buyer
            ON orders(buyer_id)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_store
            ON orders(store_id)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_status
            ON orders(status)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_receiver
            ON messages(receiver_id)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user
            ON notifications(user_id)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_seller
            ON financial_transactions(seller_id)
        """)


        db.commit()

        print("VYORA database initialized successfully.")


    finally:

        db.close()


# ==========================================================
# STARTUP
# ==========================================================

if __name__ == "__main__":
    init_db()
