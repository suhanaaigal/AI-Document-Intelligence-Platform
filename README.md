# AI-Document-Intelligence-Platform
AI-powered document classification, summarization, analysis, and RAG-based question answering using LLMs and vector search.

Document search uses lightweight, deterministic feature-hashing embeddings to keep memory usage low on free hosting plans. Retrieval is primarily based on matching terms and phrases; it does not load a local transformer model.

## Render deployment

Deploy this repository with the **Docker** runtime, not Render's native Python runtime. The Dockerfile installs the Tesseract OCR system executable required for image analysis. The repository's Render Blueprint (`render.yaml`) selects Docker automatically; when creating a service manually, choose **Docker** and use the root `Dockerfile`.

Set `OPENROUTER_API_KEY` in the Render service's environment settings. Do not commit the local `.env` file.
