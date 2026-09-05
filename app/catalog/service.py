from app.database import get_connection


class ProductError(Exception):
    pass


class CategoryError(Exception):
    pass


class MediaError(Exception):
    pass


VALID_FULFILLMENT_TYPES = {
    "ready_stock",
    "made_to_order",
}

VALID_MEDIA_TYPES = {
    "image",
    "video",
}

MAX_IMAGE_SIZE = 8 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024


def create_category(
    name: str,
    slug: str,
    parent_id: int | None = None,
):
    name = " ".join(str(name).split())
    slug = str(slug).strip().lower()

    if not name:
        raise CategoryError("Category name is required.")

    if len(name) > 120:
        raise CategoryError("Category name is too long.")

    if not slug:
        raise CategoryError("Category slug is required.")

    if len(slug) > 160:
        raise CategoryError("Category slug is too long.")

    connection = get_connection()

    try:
        if parent_id is not None:
            parent = connection.execute(
                """
                SELECT id
                FROM categories
                WHERE id = ?
                AND is_active = 1
                LIMIT 1
                """,
                (parent_id,),
            ).fetchone()

            if parent is None:
                raise CategoryError(
                    "Parent category not found."
                )

        existing = connection.execute(
            """
            SELECT id
            FROM categories
            WHERE slug = ?
            LIMIT 1
            """,
            (slug,),
        ).fetchone()

        if existing is not None:
            raise CategoryError(
                "A category with this slug already exists."
            )

        cursor = connection.execute(
            """
            INSERT INTO categories (
                parent_id,
                name,
                slug
            )
            VALUES (?, ?, ?)
            """,
            (
                parent_id,
                name,
                slug,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def assign_product_category(
    product_id: int,
    category_id: int,
):
    connection = get_connection()

    try:
        product = connection.execute(
            """
            SELECT id
            FROM products
            WHERE id = ?
            LIMIT 1
            """,
            (product_id,),
        ).fetchone()

        if product is None:
            raise CategoryError("Product not found.")

        category = connection.execute(
            """
            SELECT id
            FROM categories
            WHERE id = ?
            AND is_active = 1
            LIMIT 1
            """,
            (category_id,),
        ).fetchone()

        if category is None:
            raise CategoryError("Category not found.")

        connection.execute(
            """
            INSERT OR IGNORE INTO product_categories (
                product_id,
                category_id
            )
            VALUES (?, ?)
            """,
            (
                product_id,
                category_id,
            ),
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_product_categories(product_id: int):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                categories.id,
                categories.parent_id,
                categories.name,
                categories.slug,
                categories.is_active
            FROM categories
            JOIN product_categories
                ON product_categories.category_id = categories.id
            WHERE product_categories.product_id = ?
            AND categories.is_active = 1
            ORDER BY categories.name ASC
            """,
            (product_id,),
        ).fetchall()

        return [
            {
                "id": row["id"],
                "parent_id": row["parent_id"],
                "name": row["name"],
                "slug": row["slug"],
                "is_active": bool(row["is_active"]),
            }
            for row in rows
        ]

    finally:
        connection.close()


def add_product_media(
    product_id: int,
    media_type: str,
    storage_key: str,
    original_name: str = "",
    mime_type: str = "",
    file_size: int = 0,
    sort_order: int = 0,
    is_primary: bool = False,
    owner_user_id: int | None = None,
):
    media_type = str(media_type).strip().lower()
    storage_key = str(storage_key).strip()
    original_name = str(original_name).strip()
    mime_type = str(mime_type).strip().lower()

    if media_type not in VALID_MEDIA_TYPES:
        raise MediaError("Invalid media type.")

    if not storage_key:
        raise MediaError("Storage key is required.")

    try:
        file_size = int(file_size)
    except (TypeError, ValueError):
        raise MediaError("Invalid file size.")

    if file_size < 0:
        raise MediaError("File size cannot be negative.")

    if media_type == "image" and file_size > MAX_IMAGE_SIZE:
        raise MediaError("Image file is too large.")

    if media_type == "video" and file_size > MAX_VIDEO_SIZE:
        raise MediaError("Video file is too large.")

    try:
        sort_order = int(sort_order)
    except (TypeError, ValueError):
        raise MediaError("Invalid sort order.")

    if sort_order < 0:
        raise MediaError("Sort order cannot be negative.")

    connection = get_connection()

    try:
        product = connection.execute(
            """
            SELECT
                products.id,
                sellers.user_id,
                sellers.is_active,
                sellers.verification_status
            FROM products
            JOIN stores
                ON stores.id = products.store_id
            JOIN sellers
                ON sellers.id = stores.seller_id
            WHERE products.id = ?
            LIMIT 1
            """,
            (product_id,),
        ).fetchone()

        if product is None:
            raise MediaError("Product not found.")

        if owner_user_id is not None:
            if product["user_id"] != owner_user_id:
                raise MediaError(
                    "You do not own this product."
                )

        if not product["is_active"]:
            raise MediaError(
                "Seller account is inactive."
            )

        if product["verification_status"] != "approved":
            raise MediaError(
                "Seller is not approved."
            )

        if is_primary:
            connection.execute(
                """
                UPDATE product_media
                SET is_primary = 0
                WHERE product_id = ?
                """,
                (product_id,),
            )

        cursor = connection.execute(
            """
            INSERT INTO product_media (
                product_id,
                media_type,
                storage_key,
                original_name,
                mime_type,
                file_size,
                sort_order,
                is_primary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                media_type,
                storage_key,
                original_name,
                mime_type,
                file_size,
                sort_order,
                1 if is_primary else 0,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def create_product(
    store_id: int,
    name: str,
    description: str = "",
    price=0,
    stock_quantity=0,
    fulfillment_type: str = "ready_stock",
    owner_user_id: int | None = None,
):
    name = " ".join(str(name).split())
    description = " ".join(str(description).split())

    if not name:
        raise ProductError("Product name is required.")

    if len(name) > 200:
        raise ProductError("Product name is too long.")

    if len(description) > 5000:
        raise ProductError("Product description is too long.")

    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ProductError("Invalid product price.")

    if price < 0:
        raise ProductError(
            "Product price cannot be negative."
        )

    try:
        stock_quantity = int(stock_quantity)
    except (TypeError, ValueError):
        raise ProductError("Invalid stock quantity.")

    if stock_quantity < 0:
        raise ProductError(
            "Stock quantity cannot be negative."
        )

    if fulfillment_type not in VALID_FULFILLMENT_TYPES:
        raise ProductError(
            "Invalid fulfillment type."
        )

    connection = get_connection()

    try:
        store = connection.execute(
            """
            SELECT
                stores.id,
                sellers.user_id,
                sellers.is_active,
                sellers.verification_status
            FROM stores
            JOIN sellers
                ON sellers.id = stores.seller_id
            WHERE stores.id = ?
            LIMIT 1
            """,
            (store_id,),
        ).fetchone()

        if store is None:
            raise ProductError("Store not found.")

        if owner_user_id is not None:
            if store["user_id"] != owner_user_id:
                raise ProductError(
                    "You do not own this store."
                )

        if not store["is_active"]:
            raise ProductError(
                "Seller account is inactive."
            )

        if store["verification_status"] != "approved":
            raise ProductError(
                "Seller is not approved."
            )

        cursor = connection.execute(
            """
            INSERT INTO products (
                store_id,
                name,
                description,
                price,
                stock_quantity,
                fulfillment_type
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                store_id,
                name,
                description,
                price,
                stock_quantity,
                fulfillment_type,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
