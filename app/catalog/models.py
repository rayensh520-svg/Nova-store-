from dataclasses import dataclass
from typing import Optional

from app.database import get_connection


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
    def find_by_id(
        cls,
        product_id: int
    ) -> Optional["Product"]:
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
