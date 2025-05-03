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
from config import system_tech_prt, system_behavioral_prt, cover_letter_generator_prompt
from resume_builder.parser.resume_parser import read_pdf_text, parse_text_resume

from resume_builder.autocv_core import generate_final_output
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
    results = collection.query(
        query_texts=[query_text],
        n_results=top_n,
    )
    if results["documents"]:
        top_chunks = [doc for docs in results["documents"] for doc in docs][:top_n]
        return top_chunks
    return ["No relevant information found."]

def OpenAiCall(api_key, messages):
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

# === Resume Builder UI ===

def render_resume_builder(api_key):
    st.title("📄 Resume Builder")

    # === Load resume text ===
    resume_path = "resume_builder/demo_resume/bobby.pdf"
    if not os.path.exists(resume_path):
        st.error("❌ Resume file not found.")
        return

    try:
        resume_txt = read_pdf_text(resume_path)
        # resume_content = parse_text_resume(resume_txt)
    except Exception as e:
        st.error(f"Failed to read resume: {str(e)}")
        return

    # === Job Description Input ===
    job_description = st.text_area("Enter Job Description:", height=150)

    # === Generate Button ===
    if st.button("🚀 Generate Resume"):
        if not job_description.strip():
            st.warning("Please enter a job description.")
            return

        st.info("🔍 Matching job description with resume...")

        # === Get matching context from ChromaDB (or other logic) ===
        try:
            top_chunks = query_chunks(job_description, top_n=5)
            context = "\n\n".join(top_chunks)

            message = [
                {"role": "system", "content": "You are resume builder"},
                {"role": "user", "content": easy_generate_prompt.format(context=context, jd_txt=job_description, resume_txt=resume_txt)}
            ]

            response = OpenAiCall(message)

        except Exception as e:
            st.error(f"Chunk query failed: {str(e)}")
            return

        # === Parse resume text via LLM ===
        try:
            st.info("🤖 Generating optimized resume...")
            parsed_resume_json = parse_text_resume(response)

            message = [
                {"role": "system", "content": "You are cover letter builder"},
                {"role": "user", "content": cover_letter_generator_prompt.format(context=context, jd_txt=job_description, resume_json=resume_txt)}
            ]
            
            cover_letter = OpenAiCall(message)

            output_dir = 'resume_builder/demo_resume/created_resume'
            
            result = generate_final_output(job_description, parsed_resume_json, output_dir, 'pdf', 'both')

            st.success("✅ Resume parsed successfully!")

# === Interview UI ===

def render_interview_ui(api_key):
    st.title("🎤 Interview Assistant")

    chunk_size = st.sidebar.slider("Chunk Size:", 100, 2000, 500, 100)
    chunk_overlap = st.sidebar.slider("Chunk Overlap:", 0, 500, 50, 10)

    st.sidebar.title("Job Description")
    job_description = st.sidebar.text_area("Enter Job Description:", height=150)

    st.sidebar.title("Interview Type")
    interview_type = st.sidebar.radio("Select Interview Type:", options=["Tech Interview", "Behavioral Interview"])

    st.sidebar.title("ChromaDB Stats")
    try:
        total_chunks = collection.count()
        st.sidebar.write(f"📊 Total Chunks: {total_chunks}")
    except Exception as e:
        st.sidebar.error(f"Error fetching chunk count: {str(e)}")

    st.sidebar.title("Upload PDFs")
    uploaded_files = st.sidebar.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

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

        if interview_type == "Tech Interview":
            top_chunks = query_chunks(query_text, top_n=5)
            context = "\n\n".join(top_chunks)
            display_message(query_text, sender="user")
            st.markdown("<hr>", unsafe_allow_html=True)

            messages = [
                {"role": "system", "content": system_tech_prt.format(job_description=job_description, context=context)},
                {"role": "user", "content": f"Question: {query_text}"}
            ]

        elif interview_type == "Behavioral Interview":
            context = ""
            display_message(query_text, sender="user")
            st.markdown("<hr>", unsafe_allow_html=True)

            messages = [
                {"role": "system", "content": system_behavioral_prt.format(job_description=job_description)},
                {"role": "user", "content": f"Question: {query_text}"}
            ]

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

        st.session_state.chat_history.extend([
            {"role": "user", "content": query_text},
            {"role": "assistant", "content": streamed_response}
        ])

# === App Entry Point ===

def main():
    st.set_page_config(page_title="AI Career Assistant", layout="wide")
    st.sidebar.title("🧭 Navigation")

    # Always show these in the sidebar
    api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
    app_mode = st.sidebar.radio("Select App Mode:", options=["Interview", "Resume Builder"])

    # Always show ChromaDB stats
    st.sidebar.title("ChromaDB Stats")
    try:
        total_chunks = collection.count()
        st.sidebar.write(f"📊 Total Chunks: {total_chunks}")
    except Exception as e:
        st.sidebar.error(f"Error fetching chunk count: {str(e)}")

    # Validate API key
    if not api_key:
        st.warning("Please enter your OpenAI API key to continue.")
        return

    # Show relevant content in main area
    if app_mode == "Interview":
        render_interview_ui(api_key)
    elif app_mode == "Resume Builder":
        render_resume_builder(api_key)

if __name__ == "__main__":
    main()