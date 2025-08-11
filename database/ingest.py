import json
import glob
import psycopg2
from tqdm import tqdm
import psycopg2.extras
from datetime import datetime
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

from constants import *
from database import get_db_connection


def process_and_insert_data(conn, model):
    """ Process JSON files, chunk their content, and insert them into the database with metadata. """
    print(f"Reading JSON files from '{PRESS_RELEASES_DIR}' and chunking text...")

    records_to_insert = []
    json_files = glob.glob(os.path.join(PRESS_RELEASES_DIR, "*.json"))
    for filepath in tqdm(json_files, desc="Reading files"):
        json_data = json.load(open(filepath))

        # Extract metadata
        title = json_data.get("title")
        author = json_data.get("author")
        link = json_data.get("link")
        content_chunks = json_data.get("content")
        date_str = json_data.get("date")
        p_date = datetime.strptime(date_str, "%m-%d-%Y").date()

        # For each chunk, associate the parent document's metadata
        for chunk in content_chunks:
            records_to_insert.append({
                "content": chunk,
                "title": title,
                "author": author,
                "publish_date": p_date,
                "source_link": link
            })

    print(f"\nGenerated {len(records_to_insert)} text chunks.")

    # Separate content for embedding
    all_content = [rec["content"] for rec in records_to_insert]

    print("Generating embeddings for all chunks...")
    embeddings = model.encode(all_content, show_progress_bar=True)

    # Combine metadata with embeddings for insertion
    data_for_db = [
        (
            rec["content"],
            embedding,
            rec["title"],
            rec["author"],
            rec["publish_date"],
            rec["source_link"]
        )
        for rec, embedding in zip(records_to_insert, embeddings)
    ]

    print("Inserting data into the database...")
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO documents (content, embedding, title, author, publish_date, source_link) 
            VALUES %s
            """,
            data_for_db
        )
        conn.commit()


if __name__ == "__main__":
    print("Starting data ingestion process...")

    # 1. Initialize the embedding model
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    # 2. Connect to the database
    connection = get_db_connection()

    # 3. The embeddings from sentence-transformers are numpy arrays, not simple python lists
    register_vector(connection)

    # 4. Process files and insert into the database
    process_and_insert_data(connection, embedding_model)
    print("\nData ingestion complete!")

    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents;")
        count = cur.fetchone()[0]
        print(f"There are now {count} document chunks in the database.")

    connection.close()
    print("Database connection closed.")
