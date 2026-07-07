import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings as app_settings


class ChromaStore:
    def __init__(self):
        os.makedirs(app_settings.chroma_persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=app_settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=app_settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def collection(self):
        return self._collection

    def add(self, ids: List[str], documents: List[str], embeddings: List[List[float]], metadatas: Optional[List[dict]] = None):
        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(self, query_embedding: List[float], top_k: int = 5) -> dict:
        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    def delete_collection(self):
        self._client.delete_collection(app_settings.chroma_collection_name)

    def count(self) -> int:
        return self._collection.count()


_store: Optional[ChromaStore] = None


def get_chroma_store() -> ChromaStore:
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store
