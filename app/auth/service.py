from app.database import get_connection

from .security import hash_password
from .validation import (
normalize_email,
validate_email,
validate_full_name,
validate_password,
validate_role,
)

class RegistrationError(Exception):
pass

def register_user(
full_name: str,
email: str,
password: str,
role: str = "buyer",
):
full_name = " ".join(full_name.split())
email = normalize_email(email)

if not validate_full_name(full_name):
    raise RegistrationError("Invalid full name.")

if not validate_email(email):
    raise RegistrationError("Invalid email address.")

if not validate_password(password):
    raise RegistrationError(
        "Password must contain at least 8 characters."
    )

if not validate_role(role):
    raise RegistrationError("Invalid account role.")

password_hash = hash_password(password)

connection = get_connection()

try:
    existing_user = connection.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        LIMIT 1
        """,
        (email,),
    ).fetchone()

    if existing_user is not None:
        raise RegistrationError(
            "An account with this email already exists."
        )

    cursor = connection.execute(
        """
        INSERT INTO users (
            full_name,
            email,
            password_hash,
            role
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            full_name,
            email,
            password_hash,
            role,
        ),
    )

    connection.commit()

    return cursor.lastrowid

finally:
    connection.close()
