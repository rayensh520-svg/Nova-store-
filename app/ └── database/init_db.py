from .connection import get_connection


def initialize_database():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_info (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL
            )
            """
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO schema_info (id, version)
            VALUES (1, 1)
            """
        )

        connection.commit()

    finally:
        connection.close()
