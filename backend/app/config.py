from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # DeepSeek (LLM)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

    # Zhipu (Embedding)
    zhipu_api_key: str = ""
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    embedding_model: str = "embedding-3"

    # Redis (optional - falls back to in-memory if unavailable)
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600
    redis_session_ttl: int = 1800

    # Chroma
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "knowledge_base"

    # RAG
    retrieval_top_k: int = 5
    hybrid_alpha: float = 0.5
    chunk_size: int = 500
    chunk_overlap: int = 100

    # Context Window
    max_context_tokens: int = 6000
    sliding_window_size: int = 10
    summary_trigger_tokens: int = 4000

    # MCP
    mcp_server_port: int = 9000
    crm_api_url: Optional[str] = None
    ticket_api_url: Optional[str] = None
    order_api_url: Optional[str] = None

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
