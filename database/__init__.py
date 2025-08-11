import psycopg2
from constants import *


def get_db_connection():
    """ Establishes a connection to the PostgreSQL database. """
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def clear_db(connection):
    """ Make the documents DB table empty. For debugging/development purposes. """
    with connection.cursor() as cur:
        print("Clearing existing data from 'documents' table...")
        cur.execute("TRUNCATE TABLE documents RESTART IDENTITY;")
        print("Committing the TRUNCATE operation...")
        connection.commit()
