from database import get_db_connection
from constants import *


def setup_database(conn):
    """ Set up the necessary database extension and table with metadata columns. """
    with conn.cursor() as cur:
        print("Enabling pgvector extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        print("Creating 'documents' table...")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT,
                embedding VECTOR({VECTOR_DIMENSION}),
                title TEXT,
                author TEXT,
                publish_date DATE,
                source_link TEXT
            );
        """)
        conn.commit()
    print("Database setup complete.")


if __name__ == "__main__":
    print("Creating the database...")

    # 1. Connect to the database
    connection = get_db_connection()

    # 2. Set up the database table and extension
    setup_database(connection)

    connection.close()
    print("Database connection closed.")
