import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


@st.cache_resource(show_spinner="Loading document embedding model...")
def get_embeddings():
    """Load the local embedding model once, only when document indexing needs it."""
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as e:
        raise RuntimeError(
            "Document embeddings are unavailable. Install langchain-huggingface "
            "and sentence-transformers."
        ) from e

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def build_chat_model(temperature: float = 0.2):
    """Build the active LLM client from the available API key."""
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_api_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
            default_headers={
                "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8501"),
                "X-Title": "AI Document Intelligence Platform",
            },
        )

    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        from langchain_groq import ChatGroq

        return ChatGroq(
            api_key=groq_api_key,
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=temperature,
        )

    return None


def initialize_services():
    """Initialize all services without crashing when optional dependencies are absent."""
    services = {}

    try:
        services["youtube_api_key"] = os.getenv("YOUTUBE_API_KEY")
        services["youtube"] = None
        services["llm"] = None
        services["embeddings"] = None

        return services

    except Exception as e:
        raise RuntimeError(f"Service initialization failed: {str(e)}")