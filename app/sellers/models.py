from dataclasses import dataclass
from typing import Optional

from app.database import get_connection


@dataclass
class Seller:
    id: int
    user_id: int
    verification_status: str
    is_active: bool

    @classmethod
    def find_by_user_id(cls, user_id: int) -> Optional["Seller"]:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    verification_status,
                    is_active
                FROM sellers
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            if row is None:
                return None

            return cls(
                id=row["id"],
                user_id=row["user_id"],
                verification_status=row["verification_status"],
                is_active=bool(row["is_active"]),
            )

        finally:
            connection.close()
