import streamlit as st
from sentence_transformers import SentenceTransformer

from constants import *
from database.retrieve import retrieve_relevant_chunks
from generation.generation import build_prompt, get_llm_answer


# --- Page Configuration ---
st.set_page_config(
    page_title="Deutsche Telekom Q&A",
    page_icon="🇩🇪",
    layout="wide"
)


# --- Application Title ---
st.title("Deutsche Telekom Press Release Q&A")
st.write("Ask questions about Deutsche Telekom's press releases.")


# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("Retrieval Configuration")
    top_k = st.slider(label="Top K Chunks:",
                      min_value=1,
                      max_value=15,
                      value=TOP_K,
                      help="Number of chunks to retrieve from the database.")
    similarity_threshold = st.slider(label="Similarity Threshold:",
                                     min_value=0.0,
                                     max_value=1.0,
                                     value=SIMILARITY_THRESHOLD,
                                     step=0.05,
                                     help="Minimum similarity score for a chunk to be considered relevant.")


# --- Initialize Components ---
@st.cache_resource
def initialize_components():
    return SentenceTransformer(EMBEDDING_MODEL)

embedding_model = initialize_components()


# --- Main Application Logic ---
with st.form(key='question_form'):
    user_question = st.text_input("Your Question:", placeholder="e.g., What are the AI initiatives at Deutsche Telekom?")
    submit_button = st.form_submit_button(label='Get Answer')

if submit_button and user_question:
    with st.spinner("Analyzing press releases..."):
        # 1. Retrieve relevant chunks
        relevant_chunks = retrieve_relevant_chunks(query_text=user_question,
                                                   model=embedding_model,
                                                   top_k=top_k,
                                                   similarity_threshold=similarity_threshold)

        # (DEBUG) Show the debug view for retrieved chunks
        with st.expander("Show Retrieved Chunks (for debugging)"):
            st.json(relevant_chunks)

        # Early exit if there are no relevant document chunks for the user's question
        if len(relevant_chunks) == 0:
            st.warning("No relevant information found in the press releases for your query.")
        else:
            # 2. Build the prompt for the LLM
            prompt = build_prompt(user_question, relevant_chunks)

            # 3. Get the answer from the LLM
            llm_answer = get_llm_answer(prompt)

            # 4. Display the answer
            st.subheader("Answer")
            st.markdown(llm_answer)
