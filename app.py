import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils import embedding_functions
import chromadb
import openai

# Constants
CHROMA_DATA_PATH = "chroma_data/"
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "pdf_chunks"

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# Initialize embedding function
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL
)

# Ensure the collection exists
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_func,
    metadata={"hnsw:space": "cosine"},
)

# Function to process PDF
def process_pdf(file_path, chunk_size, chunk_overlap):
    """Processes the uploaded PDF file, chunks it, and stores it in ChromaDB."""
    loader = PyPDFLoader(file_path)
    document = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunked_documents = text_splitter.split_documents(document)

    documents = [doc.page_content for doc in chunked_documents]
    metadatas = [doc.metadata for doc in chunked_documents]

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=[f"id_{i}" for i in range(len(chunked_documents))],
    )
    
    return len(chunked_documents)

# Function to query ChromaDB
def query_chunks(query_text, top_n=5):
    """Queries the ChromaDB collection and returns the top N most relevant chunks."""
    results = collection.query(
        query_texts=[query_text],
        n_results=top_n,
    )
    if results["documents"]:
        return [doc[0] for doc in results["documents"]]
    return ["No relevant information found."]

# Function to call OpenAI (new SDK)
def call_openai(api_key, query_text, context):
    """Calls OpenAI API with the query and context using the new SDK."""
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. based on the context provided, answer the user's question."},
            {"role": "user", "content": f"{query_text}\n\nContext:\n{context}"},
        ],
    )
    return response.choices[0].message.content

# Function to display messages in a styled way
def display_message(message, sender="assistant"):
    icon = "🤖" if sender == "assistant" else "👤"
    alignment = "assistant" if sender == "assistant" else "user"
    st.markdown(f"""
    <div class="chat-message {alignment}">
        <div class="icon">{icon}</div>
        <div class="text">{message}</div>
    </div>
    """, unsafe_allow_html=True)

# Streamlit App
def main():
    st.set_page_config(page_title="PDF Q&A with ChromaDB", layout="centered")

    st.markdown("""
        <style>
        .chat-message {
            border: 1px solid #ccc;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            display: flex;
            max-width: 75%;
        }
        .chat-message.assistant {
            background-color: #f1f1f1;
            text-align: left;
            align-items: center;
            justify-content: left;
        }
        .chat-message.user {
            background-color: #e1f5fe;
            align-items: center;
            justify-content: left;
        }
        .chat-message .icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
        }
        .chat-message.user .icon {
            margin-left: 10px;
            margin-right: 0;
        }
        .chat-message .text {
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📄 PDF Chunker and Chatbot with ChromaDB")

    # Sidebar settings
    st.sidebar.title("⚙️ Settings")
    api_key = st.sidebar.text_input("Enter OpenAI API Key:", type="password")
    chunk_size = st.sidebar.slider("Chunk Size (characters):", min_value=100, max_value=2000, value=500, step=100)
    chunk_overlap = st.sidebar.slider("Chunk Overlap (characters):", min_value=0, max_value=500, value=50, step=10)

    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if uploaded_file is not None and api_key:
        temp_file_path = "temp_uploaded_file.pdf"
        
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.read())

        num_chunks = process_pdf(temp_file_path, chunk_size, chunk_overlap)
        
        os.remove(temp_file_path)

        st.success(f"✅ Successfully processed and stored {num_chunks} chunks from the PDF!")

    query_text = st.text_input("💬 Ask a question about the PDF:")
    
    if query_text and api_key:
        with st.spinner("Thinking..."):
            top_chunks = query_chunks(query_text, top_n=5)
            context = "\n\n".join(top_chunks)

            # Display context
            st.text_area("🔎 Top Chunks (Context):", value=context, height=150)

            openai_response = call_openai(api_key, query_text, context)

            # Display messages nicely
            display_message("Here are the top results based on your preferences:", sender="assistant")
            display_message(openai_response, sender="assistant")

if __name__ == "__main__":
    main()