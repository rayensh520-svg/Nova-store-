import sqlite3
from functools import wraps
from flask import session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "data/vyora.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def register_user(full_name, email, password, role):
    full_name = (full_name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""
    role = (role or "").strip().lower()

    if not full_name:
        return False, "الاسم الكامل مطلوب."

    if not email:
        return False, "البريد الإلكتروني مطلوب."

    if len(password) < 8:
        return False, "كلمة السر يجب أن تحتوي على 8 أحرف على الأقل."

    if role not in ("buyer", "seller"):
        return False, "نوع الحساب غير صالح."

    connection = get_connection()

    try:
        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing:
            return False, "هذا البريد الإلكتروني مسجل من قبل."

        password_hash = generate_password_hash(password)

        cursor = connection.execute(
            """
            INSERT INTO users
            (full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                full_name,
                email,
                password_hash,
                role
            )
        )

        connection.commit()

        user_id = cursor.lastrowid

        return True, {
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "role": role
        }

    except sqlite3.Error as error:
        connection.rollback()
        return False, f"Database error: {error}"

    finally:
        connection.close()


def login_user(email, password):
    email = (email or "").strip().lower()
    password = password or ""

    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT id, full_name, email, password_hash, role
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if not user:
            return False, "البريد الإلكتروني أو كلمة السر غير صحيحة."

        if not check_password_hash(user["password_hash"], password):
            return False, "البريد الإلكتروني أو كلمة السر غير صحيحة."

        session["user_id"] = user["id"]
        session["user_role"] = user["role"]
        session["user_name"] = user["full_name"]

        return True, {
            "user_id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"]
        }

    finally:
        connection.close()


def logout_user():
    session.clear()


def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "error": "Authentication required."
            }), 401

        return function(*args, **kwargs)

    return decorated_function


def seller_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "error": "Authentication required."
            }), 401

        if session.get("user_role") != "seller":
            return jsonify({
                "success": False,
                "error": "Seller access required."
            }), 403

        return function(*args, **kwargs)

    return decorated_function
