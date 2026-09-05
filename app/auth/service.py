from app.database import get_connection
from app.sellers.service import create_seller

from .security import hash_password, verify_password
from .validation import (
    normalize_email,
    validate_email,
    validate_full_name,
    validate_password,
    validate_role,
)


class RegistrationError(Exception):
    pass


class LoginError(Exception):
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

        user_id = cursor.lastrowid

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    if role == "seller":
        try:
            create_seller(user_id)
        except Exception as error:
            connection = get_connection()

            try:
                connection.execute(
                    "DELETE FROM users WHERE id = ?",
                    (user_id,),
                )
                connection.commit()
            finally:
                connection.close()

            raise RegistrationError(
                f"Seller account creation failed: {error}"
            )

    return user_id


def login_user(email: str, password: str):
    email = normalize_email(email)

    if not validate_email(email):
        raise LoginError("Invalid email or password.")

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
            (email,),
        ).fetchone()

        if row is None:
            raise LoginError("Invalid email or password.")

        if not row["is_active"]:
            raise LoginError("This account is inactive.")

        if not verify_password(password, row["password_hash"]):
            raise LoginError("Invalid email or password.")

        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
        }

    finally:
        connection.close()
