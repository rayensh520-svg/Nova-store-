from dataclasses import dataclass
from typing import Optional

from app.database import get_connection

@dataclass
class User:
id: int
full_name: str
email: str
password_hash: str
role: str
is_active: bool

@classmethod
def find_by_email(cls, email: str) -> Optional["User"]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                full_name,
                email,
                password_hash,
                role,
                is_active
            FROM users
            WHERE email = ?
            LIMIT 1
            """,
            (email.strip().lower(),),
        ).fetchone()

        if row is None:
            return None

        return cls(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
            is_active=bool(row["is_active"]),
        )

    finally:
        connection.close()
