import sys
import pysqlite3  # Important fix for Streamlit Cloud sqlite3 version
sys.modules["sqlite3"] = pysqlite3

import os
import shutil
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils import embedding_functions
import chromadb
import openai

# === Constants ===
CHROMA_DATA_PATH = "chroma_data/"
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "pdf_chunks"

# === Initialize ChromaDB ===
client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# === Initialize Embedding Function ===
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL
)

# === Create/Get Collection ===
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_func,
    metadata={"hnsw:space": "cosine"},
)

# === Functions ===

def process_pdfs(file_paths, chunk_size, chunk_overlap):
    """Processes multiple PDFs and adds chunks to ChromaDB."""
    chunk_count = 0

    for file_path in file_paths:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents(documents)

        documents_texts = [doc.page_content for doc in chunks]
        metadatas = [doc.metadata for doc in chunks]

        collection.add(
            documents=documents_texts,
            metadatas=metadatas,
            ids=[f"{os.path.basename(file_path)}_id_{i}" for i in range(len(chunks))]
        )

        chunk_count += len(chunks)

    return chunk_count

def query_chunks(query_text, top_n=5):
    """Queries ChromaDB and returns the top N relevant chunks."""
    results = collection.query(
        query_texts=[query_text],
        n_results=top_n,
    )
    if results["documents"]:
        return [doc[0] for doc in results["documents"]]
    return ["No relevant information found."]

def call_openai(api_key, query_text, context):
    """Calls OpenAI API to get a response."""
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{query_text}\n\nContext:\n{context}"},
        ],
    )
    return response.choices[0].message.content

def clear_chroma_db():
    """Completely clears ChromaDB by deleting the local folder."""
    if os.path.exists(CHROMA_DATA_PATH):
        shutil.rmtree(CHROMA_DATA_PATH)
    # Reinitialize everything
    global client, collection
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"},
    )

# === Streamlit App ===

def main():
    st.title("📄 Multi-PDF Upload and Manage ChromaDB 🔥")

    # Sidebar
    st.sidebar.title("Settings")
    api_key = st.sidebar.text_input("Enter OpenAI API Key:", type="password")
    chunk_size = st.sidebar.slider("Chunk Size:", min_value=100, max_value=2000, value=500, step=100)
    chunk_overlap = st.sidebar.slider("Chunk Overlap:", min_value=0, max_value=500, value=50, step=10)

    st.sidebar.title("ChromaDB Management")
    if st.sidebar.button("🧹 Clear All Stored PDFs"):
        clear_chroma_db()
        st.sidebar.success("Cleared all documents from ChromaDB!")

    # Upload multiple PDFs
    uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files and api_key:
        temp_file_paths = []

        for uploaded_file in uploaded_files:
            temp_path = os.path.join("temp", uploaded_file.name)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            temp_file_paths.append(temp_path)

        # Process uploaded PDFs
        with st.spinner("Processing PDFs..."):
            num_chunks = process_pdfs(temp_file_paths, chunk_size, chunk_overlap)
        
        # Clean up temp files
        for path in temp_file_paths:
            os.remove(path)

        st.success(f"✅ Processed {len(uploaded_files)} PDFs into {num_chunks} chunks!")

    # Query section
    st.subheader("💬 Ask a question about the uploaded PDFs")
    query_text = st.text_input("Your Question:")

    if query_text and api_key:
        top_chunks = query_chunks(query_text, top_n=5)
        context = "\n\n".join(top_chunks)

        st.text_area("🔍 Top Chunks:", value=context, height=200)

        # OpenAI Completion
        openai_response = call_openai(api_key, query_text, context)
        st.text_area("🤖 OpenAI's Answer:", value=openai_response, height=200)

if __name__ == "__main__":
    main()