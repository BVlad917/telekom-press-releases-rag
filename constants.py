import os


# --- Press releases scraping ---
TELEKOM_BASE_URL = "https://www.telekom.com"
PRESS_RELEASES_URL = "https://www.telekom.com/dynamic/fragment/com16/en/418728"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
PRESS_RELEASES_DIR = "./press_releases"
PRESS_RELEASES_TARGET_COUNT = 250  # 10


# --- DB configuration ---
DB_HOST = os.getenv("DB_HOST", "localhost")  # use the DB_HOST env variable if this is called from the docker-compose network
DB_PORT = "5432"
DB_NAME = "telekom_rag"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"


# --- Embeddings ---
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
VECTOR_DIMENSION = 384


# --- Retrieval ---
TOP_K = 5  # How many similar document chunks to retrieve from the DB
SIMILARITY_THRESHOLD = 0.5  # What is the minimum similarity above which we consider that a document is relevant to a question


# --- Generation ---
OPENAI_LLM_MODEL = "gpt-4-turbo"
OPENAI_KEY=""
LLM_MAX_OUTPUT_TOKENS = 1024
LLM_TEMPERATURE = 0.0
