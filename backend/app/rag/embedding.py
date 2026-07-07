from typing import List
import tiktoken
from openai import OpenAI
from app.config import settings


class EmbeddingService:
    MAX_TOKENS_PER_BATCH = 8192
    MAX_TOKENS_PER_TEXT = 4096

    def __init__(self):
        self._client = OpenAI(
            api_key=settings.zhipu_api_key,
            base_url=settings.zhipu_base_url,
        )
        self._model = settings.embedding_model
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        """u7cbex786eex8ba1xe7xae97xe6xafx8fxe4xb8xaaxe6x96x87xe6x9cxaaxe7x9ax84 token xe6x95xb0xe3x80x82"""
        return len(self._encoder.encode(text))

    def _truncate_text(self, text: str) -> str:
        """u5355xe4xb8xaaxe6x96x87xe6x9cxacxe8xb6x85xe9x95xbfxe6x97xb6xe8x87xaaxe5x8aa8xe6x88xaaxe6x96xadxe3x80x82"""
        tokens = self._encoder.encode(text)
        if len(tokens) <= self.MAX_TOKENS_PER_TEXT:
            return text
        truncated = self._encoder.decode(tokens[:self.MAX_TOKENS_PER_TEXT])
        return truncated

    def _batch_texts_by_tokens(self, texts: List[str]) -> List[List[str]]:
        """u5c06xe6x96x87xe6x9cxacxe5x9dx97xe5x88x97xe8xa1xa8xe5x8axa8xe6x80x81xe5x88x86xe5x89xb2xe4xb8xbaxe5xa4x9axe4xb8xaaxe6x89xb9xe6xacxa1xefxbcx8c
        u6bcfxe4xb8xaaxe6x89xb9xe6xacxa1 token xe6x80xbbxe6x95xb0xe4xb8x8dxe8xb6x85xe8xbfx87 MAX_TOKENS_PER_BATCHxe3x80x82"""
        batches: List[List[str]] = []
        current_batch: List[str] = []
        current_tokens = 0

        for text in texts:
            truncated = self._truncate_text(text)
            text_tokens = self._count_tokens(truncated)

            # u5982xe6x9ex9c xe6x9cxacxe6x96x87xe6x89xb9xe5x8axa0xe4xb8x8axe5xbd93xe5x89x8dxe6x96x87xe6x9cxacxe4xbcx9axe8xb6x85xe9x99x90
            if current_batch and current_tokens + text_tokens > self.MAX_TOKENS_PER_BATCH:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(truncated)
            current_tokens += text_tokens

        if current_batch:
            batches.append(current_batch)

        return batches

    def embed(self, texts: List[str]) -> List[List[float]]:
        """xe6x89xb9xe9x87x8fxe5x90x91xe9x87x8fxe5x8cx96xefxbcx9axe8x87xaaxe5x8aa8xe5x88x86xe6x89xb9 + xe6x88xaaxe6x96xad + xe5x90x88xe5xb9xb6xe3x80x82"""
        if not texts:
            return []

        batches = self._batch_texts_by_tokens(texts)
        all_embeddings: List[List[float]] = []

        for batch in batches:
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            all_embeddings.extend(d.embedding for d in response.data)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        truncated = self._truncate_text(text)
        return self.embed([truncated])[0]


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
