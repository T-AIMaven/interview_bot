import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # OPENAI_MODEL_ID: str = st.secrets.OPENAI_MODEL_ID
    # OPENAI_API_KEY: str = st.secrets.OPENAI_API_KEY
    # DATASET_FILE: str = st.secrets.DATASET_FILE
    
    OPENAI_MODEL_ID: str = os.getenv("OPENAI_MODEL_ID")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    DATASET_FILE: str = os.getenv("DATASET_FILE")
    
settings = Settings()