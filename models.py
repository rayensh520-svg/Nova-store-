import sqlite3
from database import get_connection


# =========================================================
# USER
# =========================================================

class User:

    @staticmethod
    def create(
        full_name,
        email,
        password,
        role="buyer",
        phone="",
        profile_image=""
    ):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO users
                (
                    full_name,
                    email,
                    password,
                    role,
                    phone,
                    profile_image
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    full_name,
                    email,
                    password,
                    role,
                    phone,
                    profile_image
                )
            )

            connection.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            return None

        finally:
            connection.close()

    @staticmethod
    def find_by_email(email):
        connection = get_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        connection.close()
        return user

    @staticmethod
    def find_by_id(user_id):
        connection = get_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        connection.close()
        return user

    @staticmethod
    def update_profile(
        user_id,
        full_name=None,
        phone=None,
        profile_image=None
    ):
        connection = get_connection()

        fields = []
        values = []

        if full_name is not None:
            fields.append("full_name = ?")
            values.append(full_name)

        if phone is not None:
            fields.append("phone = ?")
            values.append(phone)

        if profile_image is not None:
            fields.append("profile_image = ?")
            values.append(profile_image)

        if fields:
            values.append(user_id)

            connection.execute(
                f"""
                UPDATE users
                SET {", ".join(fields)}
                WHERE id = ?
                """,
                values
            )

            connection.commit()

        connection.close()

    @staticmethod
    def update_settings(
        user_id,
        language=None,
        dark_mode=None,
        notifications_enabled=None
    ):
        connection = get_connection()

        fields = []
        values = []

        if language is not None:
            fields.append("language = ?")
            values.append(language)

        if dark_mode is not None:
            fields.append("dark_mode = ?")
            values.append(int(bool(dark_mode)))

        if notifications_enabled is not None:
            fields.append("notifications_enabled = ?")
            values.append(int(bool(notifications_enabled)))

        if fields:
            values.append(user_id)

            connection.execute(
                f"""
                UPDATE users
                SET {", ".join(fields)}
                WHERE id = ?
                """,
                values
            )

            connection.commit()

        connection.close()

    @staticmethod
    def verify_phone(user_id):
        connection = get_connection()

        connection.execute(
            """
            UPDATE users
            SET phone_verified = 1
            WHERE id = ?
            """,
            (user_id,)
        )

        connection.commit()
        connection.close()


# =========================================================
# STORE
# =========================================================

class Store:

    @staticmethod
    def create(
        user_id,
        name,
        description="",
        phone="",
        wilaya="",
        municipality=""
    ):
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO stores
                (
                    user_id,
                    name,
                    description,
                    phone,
                    wilaya,
                    municipality
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    description,
                    phone,
                    wilaya,
                    municipality
                )
            )

            connection.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            return None

        finally:
            connection.close()

    @staticmethod
    def find_by_user_id(user_id):
        connection = get_connection()

        store = connection.execute(
            """
            SELECT *
            FROM stores
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        connection.close()
        return store

    @staticmethod
    def find_by_id(store_id):
        connection = get_connection()

        store = connection.execute(
            """
            SELECT *
            FROM stores
            WHERE id = ?
            """,
            (store_id,)
        ).fetchone()

        connection.close()
        return store

    @staticmethod
    def update(
        store_id,
        name=None,
        description=None,
        phone=None,
        wilaya=None,
        municipality=None,
        logo=None,
        cover_image=None,
        opening_hours=None
    ):
        connection = get_connection()

        fields = []
        values = []

        data = {
            "name": name,
            "description": description,
            "phone": phone,
            "wilaya": wilaya,
            "municipality": municipality,
            "logo": logo,
            "cover_image": cover_image,
            "opening_hours": opening_hours
        }

        for field, value in data.items():
            if value is not None:
                fields.append(f"{field} = ?")
                values.append(value)
# ============================================================
# DZ MARKET - CHAT SETTINGS
# ============================================================

class ChatSettings:

    @staticmethod
    def get(user_id):
        connection = get_connection()

        row = connection.execute(
            """
            SELECT *
            FROM chat_settings
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        if row is None:
            connection.execute(
                """
                INSERT INTO chat_settings
                (user_id, voice_type, voice_enabled, language, style)
                VALUES (?, 'female', 1, 'ar', 'friendly')
                """,
                (user_id,)
            )

            connection.commit()

            row = connection.execute(
                """
                SELECT *
                FROM chat_settings
                WHERE user_id = ?
                """,
                (user_id,)
            ).fetchone()

        connection.close()

        return row


    @staticmethod
    def update(
        user_id,
        voice_type=None,
        voice_enabled=None,
        language=None,
        style=None
    ):
        current = ChatSettings.get(user_id)

        new_voice_type = (
            voice_type
            if voice_type in ("female", "male")
            else current["voice_type"]
        )

        new_voice_enabled = (
            int(bool(voice_enabled))
            if voice_enabled is not None
            else current["voice_enabled"]
        )

        new_language = (
            language
            if language in ("ar", "fr", "en")
            else current["language"]
        )

        allowed_styles = (
            "friendly",
            "youthful",
            "funny",
            "professional",
            "darija"
        )

        new_style = (
            style
            if style in allowed_styles
            else current["style"]
        )

        connection = get_connection()

        connection.execute(
            """
            UPDATE chat_settings
            SET
                voice_type = ?,
                voice_enabled = ?,
                language = ?,
                style = ?
            WHERE user_id = ?
            """,
            (
                new_voice_type,
                new_voice_enabled,
                new_language,
                new_style,
                user_id
            )
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM chat_settings
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        connection.close()

        return row
