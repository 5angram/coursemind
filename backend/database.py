import os 

import psycopg2

def get_db_connection():
    """Create and return a PostgreSQL connection."""

    password = os.getenv("COURSEMIND_DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "COURSEMIND_DB_PASSWORD environment variable is not set."
        )

    connection = psycopg2.connect(
        host = "127.0.0.1",
        port = 5432,
        dbname="coursemind",
        user="postgres",
        password=password,
        connect_timeout=5,
    )

    return connection