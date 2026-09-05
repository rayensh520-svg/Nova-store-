from dataclasses import dataclass
from typing import Optional

from app.database import get_connection


@dataclass
class Store:
    id: int
    seller_id: int
    name: str
    description: str
    is_visible: bool

    @classmethod
    def find_by_seller_id(
        cls,
        seller_id: int
    ) -> Optional["Store"]:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    seller_id,
                    name,
                    description,
                    is_visible
                FROM stores
                WHERE seller_id = ?
                LIMIT 1
                """,
                (seller_id,),
            ).fetchone()

            if row is None:
                return None

            return cls(
                id=row["id"],
                seller_id=row["seller_id"],
                name=row["name"],
                description=row["description"] or "",
                is_visible=bool(row["is_visible"]),
            )

        finally:
            connection.close()

    @classmethod
    def find_by_id(
        cls,
        store_id: int
    ) -> Optional["Store"]:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    seller_id,
                    name,
                    description,
                    is_visible
                FROM stores
                WHERE id = ?
                LIMIT 1
                """,
                (store_id,),
            ).fetchone()

            if row is None:
                return None

            return cls(
                id=row["id"],
                seller_id=row["seller_id"],
                name=row["name"],
                description=row["description"] or "",
                is_visible=bool(row["is_visible"]),
            )

        finally:
            connection.close()
