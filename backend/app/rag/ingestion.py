import os
from typing import List
from app.rag.chunker import chunk_documents
from app.rag.embedding import get_embedding_service
from app.rag.vector_store import get_chroma_store


def load_documents_from_dir(directory: str) -> dict[str, str]:
    docs: dict[str, str] = {}
    if not os.path.isdir(directory):
        return docs
    for filename in os.listdir(directory):
        if filename.endswith((".txt", ".md", ".csv")):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                docs[filename] = f.read()
    return docs


async def ingest_documents(directory: str | None = None) -> int:
    store = get_chroma_store()
    embedder = get_embedding_service()

    if directory is None:
        # ingestion.py is at backend/app/rag/ingestion.py
        # Go up 4 levels to reach project root, then knowledge_docs
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        directory = os.path.join(project_root, "knowledge_docs")
        if not os.path.isdir(directory):
            # Fallback: try relative path
            directory = os.path.join(os.getcwd(), "knowledge_docs")
        if not os.path.isdir(directory):
            # Fallback: try backend/knowledge_docs
            directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "knowledge_docs")

    raw_docs = load_documents_from_dir(directory)
    if not raw_docs:
        return 0

    chunks = chunk_documents(raw_docs)
    if not chunks:
        return 0

    texts = [c["content"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [{"doc_id": c["doc_id"]} for c in chunks]

    embeddings = embedder.embed(texts)
    store.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    return len(chunks)


def ingest_documents_sync(directory: str | None = None) -> int:
    import asyncio
    return asyncio.run(ingest_documents(directory))
