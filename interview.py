# === PyTorch/Streamlit Watcher Fix (MUST BE FIRST) ===
import os
try:
    import torch
    if hasattr(torch.classes, '__path__'):
        torch.classes.__path__ = [os.path.join(torch.__path__[0], "classes")]
except ImportError:
    pass

# === Standard Imports ===
import shutil
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils import embedding_functions
import chromadb
from openai import OpenAI
import time
from config import system_tech_prt, system_behavioral_prt

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

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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
        top_chunks = [doc for docs in results["documents"] for doc in docs][:top_n]
        return top_chunks
    return ["No relevant information found."]

def OpenAiCall(api_key, messages):
    """Calls OpenAI API with proper streaming handling."""
    client = OpenAI(api_key=api_key, timeout=20.0)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
                    
    except Exception as e:
        yield f"⚠️ Error: {str(e)}"

def display_message(message, sender="assistant"):
    icon = "🤖" if sender == "assistant" else "👤"
    alignment = "assistant" if sender == "assistant" else "user"
    st.markdown(f"""
        <div class="chat-message {alignment}">
            <div class="icon">{icon}</div>
            <div class="text">{message}</div>
        </div>
    """, unsafe_allow_html=True)

# === Streamlit App ===

def main():
    # Sidebar
    st.sidebar.title("Settings")
    api_key = st.sidebar.text_input("Enter OpenAI API Key:", type="password")
    chunk_size = st.sidebar.slider("Chunk Size:", 100, 2000, 500, 100)
    chunk_overlap = st.sidebar.slider("Chunk Overlap:", 0, 500, 50, 10)

    # Job Description Input in Sidebar
    st.sidebar.title("Job Description")
    job_description = st.sidebar.text_area("Enter Job Description:", height=150)

    # Interview Type Selection
    st.sidebar.title("Interview Type")
    interview_type = st.sidebar.radio(
        "Select Interview Type:",
        options=["Tech Interview", "Behavioral Interview"]
    )

    # Count and Display Total Chunks in Sidebar
    st.sidebar.title("ChromaDB Stats")
    try:
        total_chunks = collection.count()  # Count all chunks in the collection
        st.sidebar.write(f"📊 Total Chunks: {total_chunks}")
    except Exception as e:
        st.sidebar.error(f"Error fetching chunk count: {str(e)}")


    # File Upload in Sidebar
    st.sidebar.title("Upload PDFs")
    uploaded_files = st.sidebar.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

    # Process Uploaded Files
    if uploaded_files and api_key:
        if not api_key.startswith('sk-'):
            st.error("❌ Invalid OpenAI API key format")
            return

        temp_file_paths = []
        for uploaded_file in uploaded_files:
            temp_path = os.path.join("temp", uploaded_file.name)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            temp_file_paths.append(temp_path)

        with st.spinner("Processing PDFs..."):
            num_chunks = process_pdfs(temp_file_paths, chunk_size, chunk_overlap)
        
        for path in temp_file_paths:
            os.remove(path)
        
        st.success(f"✅ Processed {len(uploaded_files)} PDF(s) into {num_chunks} chunks!")

    query_text = st.text_input("Your Question:", key="query_input")
    
    if query_text and api_key:
        start_time = time.time()

        # Handle Tech Interview
        if interview_type == "Tech Interview":
            top_chunks = query_chunks(query_text, top_n=5)
            print("Top chunks:", top_chunks)
            context = "\n\n".join(top_chunks)

            # Display the user's question
            display_message(query_text, sender="user")
            st.markdown("<hr>", unsafe_allow_html=True)

            # FIXED MESSAGE FORMATTING
            messages = [
                {"role": "system", "content": system_tech_prt.format(job_description=job_description, context=context)},
                {"role": "user", "content": f"Question: {query_text}"}
            ]

        # Handle Behavioral Interview
        elif interview_type == "Behavioral Interview":
            # Use a simple prompt for behavioral questions
            context = ""
            display_message(query_text, sender="user")
            st.markdown("<hr>", unsafe_allow_html=True)

            # FIXED MESSAGE FORMATTING
            messages = [
                {"role": "system", "content": system_behavioral_prt.format(job_description=job_description)},
                {"role": "user", "content": f"Question: {query_text}"}
            ]

        # Streaming Response
        response_placeholder = st.empty()
        streamed_response = ""
        
        try:
            for chunk in OpenAiCall(api_key, messages):
                streamed_response += chunk
                response_placeholder.markdown(
                    f"<div style='font-size:18px; line-height:1.6; max-width: 400px; padding: 20px;'>{streamed_response}▌</div>",
                    unsafe_allow_html=True
                )
            
            response_placeholder.markdown(
                f"<div style='font-size:18px; line-height:1.6; max-width: 400px; padding: 20px;'>{streamed_response}</div>",
                unsafe_allow_html=True
            )
            end_time = time.time()
            print(f"Response time: {end_time - start_time:.2f} seconds")
        except Exception as e:
            st.error(f"🚨 Streaming Error: {str(e)}")
            return

        # Update chat history
        st.session_state.chat_history.extend([
            {"role": "user", "content": query_text},
            {"role": "assistant", "content": streamed_response}
        ])

if __name__ == "__main__":
    main()