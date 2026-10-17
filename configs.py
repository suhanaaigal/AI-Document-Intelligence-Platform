import os
import hashlib
import math
import re
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
import streamlit as st

load_dotenv()


class LightweightEmbeddings(Embeddings):
    def __init__(self, dimensions: int = 2048):
        self.dimensions = dimensions

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        tokens = re.findall(r"\w+", text.lower())
        vector = [0.0] * self.dimensions
        features = []

        for token in tokens:
            features.append(("word:" + token, 1.0))
            if len(token) >= 3:
                features.extend(
                    ("char:" + token[index:index + 3], 0.25)
                    for index in range(len(token) - 2)
                )

        features.extend(
            ("pair:" + left + "_" + right, 0.5)
            for left, right in zip(tokens, tokens[1:])
        )

        for feature, weight in features:
            digest = hashlib.blake2b(
                feature.encode("utf-8"), digest_size=8
            ).digest()
            value = int.from_bytes(digest, "little")
            index = value % self.dimensions
            vector[index] += weight if value & (1 << 63) else -weight

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude:
            vector = [value / magnitude for value in vector]
        return vector


@st.cache_resource(show_spinner="Preparing lightweight document search...")
def get_embeddings():
    """Create a small deterministic text embedder without loading ML frameworks."""
    return LightweightEmbeddings()


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