import re
from typing import List
from app.config import settings


class SemanticChunker:
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def _split_paragraphs(self, text: str) -> List[str]:
        paragraphs = re.split(r"\n\s*\n", text.strip())
        return [p.strip() for p in paragraphs if p.strip()]

    def _sliding_window(self, paragraphs: List[str]) -> List[str]:
        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)
            if current_len + para_len > self.chunk_size and current:
                chunks.append("\n\n".join(current))
                overlap_point = max(0, len(current) - 1)
                current = current[overlap_point:]
                current_len = sum(len(p) for p in current)
            current.append(para)
            current_len += para_len

        if current:
            chunks.append("\n\n".join(current))

        return chunks

    def chunk(self, text: str) -> List[str]:
        paragraphs = self._split_paragraphs(text)
        if not paragraphs:
            return []
        return self._sliding_window(paragraphs)


def chunk_documents(documents: dict[str, str]) -> list[dict[str, str]]:
    chunker = SemanticChunker()
    all_chunks: list[dict[str, str]] = []
    for doc_id, content in documents.items():
        chunks = chunker.chunk(content)
        for i, chunk_text in enumerate(chunks):
            all_chunks.append({
                "chunk_id": f"{doc_id}_chunk_{i}",
                "doc_id": doc_id,
                "content": chunk_text,
            })
    return all_chunks
