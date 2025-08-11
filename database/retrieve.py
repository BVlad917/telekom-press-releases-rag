from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

from constants import *
from database import get_db_connection


def retrieve_relevant_chunks(query_text: str, model: SentenceTransformer, top_k: int, similarity_threshold: float) -> list[dict]:
    """
    Retrieve the top_k most relevant document chunks that are above the similarity threshold.
    """
    # 1. Connect to the database
    conn = get_db_connection()
    register_vector(conn)

    # 2. Generate the embedding for the user's query
    query_embedding = model.encode(query_text)

    # 3. Perform the vector similarity search
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content, title, author, publish_date, source_link, 1 - (embedding <=> %s) AS similarity
            FROM documents
            WHERE 1 - (embedding <=> %s) >= %s
            ORDER BY similarity DESC
            LIMIT %s;
            """,
            (query_embedding, query_embedding, similarity_threshold, top_k)
        )
        results = cur.fetchall()

    # 4. Format the results into a more usable list of dictionaries
    relevant_chunks = []
    for row in results:
        relevant_chunks.append({
            "content": row[0],
            "title": row[1],
            "author": row[2],
            "publish_date": row[3].strftime("%Y-%m-%d"),
            "source_link": row[4],
            "similarity": row[5]
        })

    return relevant_chunks


if __name__ == "__main__":
    print("Initializing embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # --- Test Case 1: A specific query ---
    test_query_1 = "What are the AI initiatives at Deutsche Telekom?"
    print(f"\n--- Testing with query: '{test_query_1}' ---")

    retrieved_chunks_1 = retrieve_relevant_chunks(test_query_1, model, top_k=TOP_K, similarity_threshold=SIMILARITY_THRESHOLD)

    if len(retrieved_chunks_1) > 0:
        print(f"\nFound {len(retrieved_chunks_1)} relevant chunks:")
        for i, chunk in enumerate(retrieved_chunks_1):
            print(f"\n--- Chunk {i + 1} (Similarity: {chunk['similarity']:.4f}) ---")
            print(f"  Source: {chunk['title']}")
            print(f"  Link: {chunk['source_link']}")
            print(f"  Published: {chunk['publish_date']}")
            print(f"  Author: {chunk['author']}")
            print(f'  Content:\n"{chunk["content"]}"')
    else:
        print("No relevant chunks found above the similarity threshold.")

    # --- Test Case 2: An off-topic query that should be filtered out ---
    test_query_2 = "What is the square root of pi?"
    print(f"\n\n--- Testing with query: '{test_query_2}' ---")

    retrieved_chunks_2 = retrieve_relevant_chunks(test_query_2, model, top_k=TOP_K, similarity_threshold=SIMILARITY_THRESHOLD)

    if len(retrieved_chunks_2) > 0:
        print(f"\nFound {len(retrieved_chunks_2)} relevant chunks:")
        for i, chunk in enumerate(retrieved_chunks_2):
            print(f"\n--- Chunk {i + 1} (Similarity: {chunk['similarity']:.4f}) ---")
            print(f"  Source: {chunk['title']}")
            print(f"  Link: {chunk['source_link']}")
            print(f"  Published: {chunk['publish_date']}")
            print(f"  Author: {chunk['author']}")
            print(f"  Content:\n'{chunk['content']}'")
    else:
        print("No relevant chunks found above the similarity threshold.")
