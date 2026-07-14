from app.config import get_settings
from app.utils.errors import EmbeddingError, LLMError


class EmbeddingService:
    def __init__(self):
        self.settings = get_settings()
        self._embeddings = None

    def _get_embeddings(self):
        if self._embeddings is not None:
            return self._embeddings

        provider = self.settings.embedding_provider.lower()

        if provider == "openai":
            from langchain_openai import OpenAIEmbeddings

            self._embeddings = OpenAIEmbeddings(
                model=self.settings.embedding_model,
                openai_api_key=self.settings.openai_api_key,
                openai_api_base=self.settings.openai_api_base,
                dimensions=self.settings.embedding_dimensions,
            )
        elif provider == "azure":
            from langchain_openai import AzureOpenAIEmbeddings

            self._embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                api_version=self.settings.azure_openai_api_version,
                azure_deployment=self.settings.azure_openai_deployment or self.settings.embedding_model,
            )
        elif provider == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=self.settings.embedding_model,
                google_api_key=self.settings.google_api_key,
            )
        elif provider == "voyage":
            from langchain_community.embeddings import VoyageEmbeddings

            self._embeddings = VoyageEmbeddings(
                voyage_api_key=self.settings.voyage_api_key,
                model=self.settings.embedding_model,
            )
        elif provider == "openrouter":
            from langchain_openai import OpenAIEmbeddings

            self._embeddings = OpenAIEmbeddings(
                model=self.settings.embedding_model,
                openai_api_key=self.settings.openrouter_api_key,
                openai_api_base=self.settings.openrouter_api_base,
                dimensions=self.settings.embedding_dimensions,
            )
        else:
            raise EmbeddingError(f"Unsupported embedding provider: {provider}")

        return self._embeddings

    def _friendly_embedding_error(self, exc: Exception) -> str:
        message = str(exc)
        lower = message.lower()
        if "401" in message or "user not found" in lower or "invalid" in lower and "api" in lower:
            provider = self.settings.embedding_provider
            return (
                f"Embedding provider authentication failed ({provider}). "
                "Check OPENROUTER_API_KEY (or your embedding provider key) in .env."
            )
        if "429" in message or "rate limit" in lower:
            return "Embedding provider rate limit reached. Wait a moment and try again."
        return f"Failed to process document embeddings: {message}"

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            embeddings = self._get_embeddings()
            return await embeddings.aembed_documents(texts)
        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError(self._friendly_embedding_error(exc)) from exc

    async def embed_query(self, text: str) -> list[float]:
        try:
            embeddings = self._get_embeddings()
            return await embeddings.aembed_query(text)
        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError(self._friendly_embedding_error(exc)) from exc


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
