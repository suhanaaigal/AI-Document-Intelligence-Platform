import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.cloud import vision
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()


def initialize_services():
    """Initialize all services"""
    services = {}

    try:
        # Environment variables
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        groq_api_key = os.getenv("GROQ_API_KEY")

        # YouTube API
        if youtube_api_key:
            services["youtube"] = build(
                "youtube",
                "v3",
                developerKey=youtube_api_key
            )

        # Groq LLM
        services["llm"] = ChatGroq(
            api_key=groq_api_key,
            model="llama-3.3-70b-versatile"
        )

        # Local Embeddings
        services["embeddings"] = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Google Vision API
        services["vision"] = vision.ImageAnnotatorClient()

        return services

    except Exception as e:
        raise RuntimeError(f"Service initialization failed: {str(e)}")