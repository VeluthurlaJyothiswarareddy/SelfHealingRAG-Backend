from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load .env from backend/ root, regardless of where uvicorn is started.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "self_healing_rag"

    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"

    groq_api_key: str = ""
    llm_provider: str = "groq"

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_deployment: str = ""

    google_api_key: str = ""
    voyage_api_key: str = ""

    openrouter_api_key: str = ""
    openrouter_api_base: str = "https://openrouter.ai/api/v1"

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    chat_model: str = "llama-3.3-70b-versatile"
    chat_temperature: float = 0.0

    max_retries: int = 3
    top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_upload_mb: int = 20
    vector_index_name: str = "vector_index"

    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    admin_key: str = "admin-secret"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def chat_api_key(self) -> str:
        if self.llm_provider.lower() == "groq":
            return self.groq_api_key
        return self.openai_api_key

    @property
    def chat_api_base(self) -> str:
        if self.llm_provider.lower() == "groq":
            return "https://api.groq.com/openai/v1"
        if self.llm_provider.lower() == "openrouter":
            return self.openrouter_api_base
        return self.openai_api_base

    @property
    def embedding_api_key(self) -> str:
        provider = self.embedding_provider.lower()
        if provider == "openrouter":
            return self.openrouter_api_key
        if provider == "openai":
            return self.openai_api_key
        return ""

    @property
    def embedding_api_base(self) -> str:
        if self.embedding_provider.lower() == "openrouter":
            return self.openrouter_api_base
        return self.openai_api_base


@lru_cache
def get_settings() -> Settings:
    return Settings()
