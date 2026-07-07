from typing import List
import json
import hashlib
import redis.asyncio as aioredis
from rank_bm25 import BM25Okapi
import jieba

from app.config import settings
from app.rag.vector_store import get_chroma_store
from app.rag.embedding import get_embedding_service


class HybridRetriever:
    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._bm25 = None
        self._bm25_docs: List[str] = []
        self._bm25_initialized = False

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    def _tokenize(self, text: str) -> List[str]:
        return list(jieba.cut(text))

    def _ensure_bm25(self):
        if self._bm25_initialized:
            return
        store = get_chroma_store()
        if store.count() == 0:
            self._bm25_initialized = True
            return
        results = store.collection.get(include=["documents"])
        self._bm25_docs = results.get("documents", [])
        tokenized = [self._tokenize(doc) for doc in self._bm25_docs]
        self._bm25 = BM25Okapi(tokenized)
        self._bm25_initialized = True

    def _cache_key(self, query: str) -> str:
        return f"rag:cache:{hashlib.md5(query.encode()).hexdigest()}"

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        alpha: float | None = None,
    ) -> List[dict]:
        top_k = top_k or settings.retrieval_top_k
        alpha = alpha or settings.hybrid_alpha

        redis = await self._get_redis()
        cached = await redis.get(self._cache_key(query))
        if cached:
            return json.loads(cached)

        embedder = get_embedding_service()
        query_embedding = embedder.embed_query(query)

        store = get_chroma_store()
        dense_results = store.query(query_embedding, top_k=top_k * 2)

        dense_docs: List[str] = dense_results.get("documents", [[]])[0]
        dense_distances: List[float] = dense_results.get("distances", [[]])[0]
        dense_metadatas: List[dict] = dense_results.get("metadatas", [[]])[0]

        self._ensure_bm25()
        bm25_scores: List[float] = []
        bm25_docs_list: List[str] = []

        if self._bm25 is not None:
            tokenized_query = self._tokenize(query)
            scores = self._bm25.get_scores(tokenized_query)
            indexed = [(i, s) for i, s in enumerate(scores)]
            indexed.sort(key=lambda x: x[1], reverse=True)
            for idx, score in indexed[:top_k * 2]:
                bm25_scores.append(score)
                bm25_docs_list.append(self._bm25_docs[idx])

        fused: dict[str, float] = {}
        doc_map: dict[str, dict] = {}

        max_dense = max(dense_distances) if dense_distances else 1.0
        for doc_text, dist, meta in zip(dense_docs, dense_distances, dense_metadatas):
            norm_score = 1.0 - (dist / max_dense) if max_dense > 0 else 1.0
            fused[doc_text] = alpha * norm_score
            doc_map[doc_text] = {"content": doc_text, "metadata": meta or {}, "score": norm_score}

        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        for doc_text, score in zip(bm25_docs_list, bm25_scores):
            norm_score = score / max_bm25 if max_bm25 > 0 else 0.0
            existing = fused.get(doc_text, 0.0)
            fused[doc_text] = existing + (1 - alpha) * norm_score
            if doc_text not in doc_map:
                doc_map[doc_text] = {"content": doc_text, "metadata": {}, "score": norm_score}
            else:
                doc_map[doc_text]["score"] = fused[doc_text]

        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)
        results = [doc_map[doc] for doc, _ in ranked[:top_k]]

        await redis.setex(self._cache_key(query), settings.redis_cache_ttl, json.dumps(results, ensure_ascii=False))
        return results


_retriever: HybridRetriever | None = None


def get_hybrid_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever
