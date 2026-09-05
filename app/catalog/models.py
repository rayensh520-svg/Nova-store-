from dataclasses import dataclass
from typing import Optional

from app.database import get_connection


@dataclass
class Category:
    id: int
    parent_id: Optional[int]
    name: str
    slug: str
    is_active: bool

    @classmethod
    def find_by_id(cls, category_id: int):
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    parent_id,
                    name,
                    slug,
                    is_active
                FROM categories
                WHERE id = ?
                LIMIT 1
                """,
                (category_id,),
            ).fetchone()

            if row is None:
                return None

            return cls(
                id=row["id"],
                parent_id=row["parent_id"],
                name=row["name"],
                slug=row["slug"],
                is_active=bool(row["is_active"]),
            )

        finally:
            connection.close()

    @classmethod
    def find_by_slug(cls, slug: str):
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    parent_id,
                    name,
                    slug,
                    is_active
                FROM categories
                WHERE slug = ?
                LIMIT 1
                """,
                (slug.strip().lower(),),
            ).fetchone()

            if row is None:
                return None

            return cls(
                id=row["id"],
                parent_id=row["parent_id"],
                name=row["name"],
                slug=row["slug"],
                is_active=bool(row["is_active"]),
            )

        finally:
            connection.close()

    @classmethod
    def list_active(cls):
        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT
                    id,
                    parent_id,
                    name,
                    slug,
                    is_active
                FROM categories
                WHERE is_active = 1
                ORDER BY
                    parent_id IS NOT NULL,
                    name ASC
                """
            ).fetchall()

            return [
                cls(
                    id=row["id"],
                    parent_id=row["parent_id"],
                    name=row["name"],
                    slug=row["slug"],
                    is_active=bool(row["is_active"]),
                )
                for row in rows
            ]

        finally:
            connection.close()


@dataclass
class ProductMedia:
    id: int
    product_id: int
    media_type: str
    storage_key: str
    original_name: str
    mime_type: str
    file_size: int
    sort_order: int
    is_primary: bool
    is_active: bool

    @classmethod
    def list_by_product(
        cls,
        product_id: int,
        active_only: bool = True
    ):
        connection = get_connection()

        try:
            query = """
                SELECT
                    id,
                    product_id,
                    media_type,
                    storage_key,
                    original_name,
                    mime_type,
                    file_size,
                    sort_order,
                    is_primary,
                    is_active
                FROM product_media
                WHERE product_id = ?
            """

            params = [product_id]

            if active_only:
                query += " AND is_active = 1"

            query += """
                ORDER BY
                    is_primary DESC,
                    sort_order ASC,
                    id ASC
            """

            rows = connection.execute(
                query,
                params,
            ).fetchall()

            return [
                cls(
                    id=row["id"],
                    product_id=row["product_id"],
                    media_type=row["media_type"],
                    storage_key=row["storage_key"],
                    original_name=row["original_name"] or "",
                    mime_type=row["mime_type"] or "",
                    file_size=int(row["file_size"]),
                    sort_order=int(row["sort_order"]),
                    is_primary=bool(row["is_primary"]),
                    is_active=bool(row["is_active"]),
                )
                for row in rows
            ]

        finally:
            connection.close()


@dataclass
class Product:
    id: int
    store_id: int
    name: str
    description: str
    price: float
    stock_quantity: int
    fulfillment_type: str
    is_active: bool

    @classmethod
    def find_by_id(cls, product_id: int):
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    store_id,
                    name,
                    description,
                    price,
                    stock_quantity,
                    fulfillment_type,
                    is_active
                FROM products
                WHERE id = ?
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()

            if row is None:
                return None

            return cls(
                id=row["id"],
                store_id=row["store_id"],
                name=row["name"],
                description=row["description"] or "",
                price=float(row["price"]),
                stock_quantity=int(row["stock_quantity"]),
                fulfillment_type=row["fulfillment_type"],
                is_active=bool(row["is_active"]),
            )

        finally:
            connection.close()

    @classmethod
    def list_by_store(
        cls,
        store_id: int,
        active_only: bool = True
    ):
        connection = get_connection()

        try:
            query = """
                SELECT
                    id,
                    store_id,
                    name,
                    description,
                    price,
                    stock_quantity,
                    fulfillment_type,
                    is_active
                FROM products
                WHERE store_id = ?
            """

            params = [store_id]

            if active_only:
                query += " AND is_active = 1"

            query += " ORDER BY id DESC"

            rows = connection.execute(
                query,
                params,
            ).fetchall()

            return [
                cls(
                    id=row["id"],
                    store_id=row["store_id"],
                    name=row["name"],
                    description=row["description"] or "",
                    price=float(row["price"]),
                    stock_quantity=int(row["stock_quantity"]),
                    fulfillment_type=row["fulfillment_type"],
                    is_active=bool(row["is_active"]),
                )
                for row in rows
            ]

        finally:
            connection.close()
