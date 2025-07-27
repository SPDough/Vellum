import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Literal, Optional, Union

import httpx
import numpy as np
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.telemetry import business_metrics, get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer("embedding_service")
settings = get_settings()


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        pass


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama local embedding provider."""

    def __init__(self, base_url: str = None, model: str = "nomic-embed-text"):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from Ollama."""
        with tracer.start_as_current_span("ollama_embedding") as span:
            span.set_attributes(
                {
                    "embedding.provider": "ollama",
                    "embedding.model": self.model,
                    "embedding.text_count": len(texts),
                }
            )

            try:
                embeddings = []
                for text in texts:
                    response = await self.client.post(
                        "/api/embeddings", json={"model": self.model, "prompt": text}
                    )
                    response.raise_for_status()
                    result = response.json()
                    embeddings.append(result["embedding"])

                # Record metrics
                business_metrics.record_llm_call(
                    model=self.model,
                    provider="ollama",
                    tokens=sum(len(text.split()) for text in texts),
                    cost=0.0,  # Local model has no cost
                )

                span.set_attribute("embedding.success", True)
                return embeddings

            except Exception as e:
                span.set_attribute("embedding.success", False)
                span.record_exception(e)
                logger.error(f"Ollama embedding failed: {e}")
                raise

    def get_dimension(self) -> int:
        """Get embedding dimension for nomic-embed-text."""
        return 768  # nomic-embed-text dimension

    def get_model_name(self) -> str:
        return self.model


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

        # Model dimensions
        self.model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from OpenAI."""
        if not self.client:
            raise ValueError("OpenAI API key not provided")

        with tracer.start_as_current_span("openai_embedding") as span:
            span.set_attributes(
                {
                    "embedding.provider": "openai",
                    "embedding.model": self.model,
                    "embedding.text_count": len(texts),
                }
            )

            try:
                response = await self.client.embeddings.create(
                    model=self.model, input=texts
                )

                embeddings = [data.embedding for data in response.data]

                # Record metrics
                business_metrics.record_llm_call(
                    model=self.model,
                    provider="openai",
                    tokens=response.usage.total_tokens,
                    cost=self._calculate_cost(response.usage.total_tokens),
                )

                span.set_attributes(
                    {
                        "embedding.success": True,
                        "embedding.tokens_used": response.usage.total_tokens,
                    }
                )
                return embeddings

            except Exception as e:
                span.set_attribute("embedding.success", False)
                span.record_exception(e)
                logger.error(f"OpenAI embedding failed: {e}")
                raise

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.model_dimensions.get(self.model, 1536)

    def get_model_name(self) -> str:
        return self.model

    def _calculate_cost(self, tokens: int) -> float:
        """Calculate cost based on tokens (approximate)."""
        # text-embedding-3-small: $0.00002 / 1K tokens
        # text-embedding-3-large: $0.00013 / 1K tokens
        costs = {
            "text-embedding-3-small": 0.00002,
            "text-embedding-3-large": 0.00013,
            "text-embedding-ada-002": 0.0001,
        }
        rate = costs.get(self.model, 0.0001)
        return (tokens / 1000) * rate


class SentenceTransformerProvider(EmbeddingProvider):
    """Local sentence transformer provider (fallback)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None  # Lazy load

    def _load_model(self):
        """Lazy load the model."""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using sentence transformers."""
        with tracer.start_as_current_span("sentence_transformer_embedding") as span:
            span.set_attributes(
                {
                    "embedding.provider": "sentence_transformer",
                    "embedding.model": self.model_name,
                    "embedding.text_count": len(texts),
                }
            )

            try:
                self._load_model()

                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(
                    None, lambda: self.model.encode(texts).tolist()
                )

                # Record metrics (no cost for local model)
                business_metrics.record_llm_call(
                    model=self.model_name,
                    provider="sentence_transformer",
                    tokens=sum(len(text.split()) for text in texts),
                    cost=0.0,
                )

                span.set_attribute("embedding.success", True)
                return embeddings

            except Exception as e:
                span.set_attribute("embedding.success", False)
                span.record_exception(e)
                logger.error(f"Sentence transformer embedding failed: {e}")
                raise

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "all-distilroberta-v1": 768,
        }
        return dimensions.get(self.model_name, 384)

    def get_model_name(self) -> str:
        return self.model_name


class EmbeddingService:
    """Main embedding service with fallback providers."""

    def __init__(self):
        self.providers = self._initialize_providers()
        self.primary_provider = self._get_primary_provider()

    def _initialize_providers(self) -> dict:
        """Initialize all available embedding providers."""
        providers = {}

        # Try Ollama first (local, cost-effective)
        try:
            providers["ollama"] = OllamaEmbeddingProvider()
            logger.info("✅ Ollama embedding provider initialized")
        except Exception as e:
            logger.warning(f"⚠️ Ollama embedding provider failed: {e}")

        # OpenAI provider (if API key available)
        if settings.openai_api_key:
            try:
                providers["openai"] = OpenAIEmbeddingProvider()
                logger.info("✅ OpenAI embedding provider initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI embedding provider failed: {e}")

        # Sentence Transformers as fallback
        try:
            providers["sentence_transformer"] = SentenceTransformerProvider()
            logger.info("✅ Sentence Transformer embedding provider initialized")
        except Exception as e:
            logger.warning(f"⚠️ Sentence Transformer provider failed: {e}")

        if not providers:
            raise RuntimeError("No embedding providers available")

        return providers

    def _get_primary_provider(self) -> EmbeddingProvider:
        """Get the primary provider based on preferences."""
        # Preference order: Ollama -> OpenAI -> Sentence Transformers
        for provider_name in ["ollama", "openai", "sentence_transformer"]:
            if provider_name in self.providers:
                logger.info(f"Using {provider_name} as primary embedding provider")
                return self.providers[provider_name]

        raise RuntimeError("No primary embedding provider available")

    async def get_embeddings(
        self, texts: Union[str, List[str]], provider: Optional[str] = None
    ) -> List[List[float]]:
        """Get embeddings with automatic fallback."""
        if isinstance(texts, str):
            texts = [texts]

        # Choose provider
        if provider and provider in self.providers:
            chosen_provider = self.providers[provider]
        else:
            chosen_provider = self.primary_provider

        # Try primary provider first
        try:
            return await chosen_provider.get_embeddings(texts)
        except Exception as e:
            logger.warning(f"Primary provider failed: {e}, trying fallbacks...")

            # Try other providers as fallback
            for name, fallback_provider in self.providers.items():
                if fallback_provider != chosen_provider:
                    try:
                        logger.info(f"Trying fallback provider: {name}")
                        return await fallback_provider.get_embeddings(texts)
                    except Exception as fallback_error:
                        logger.warning(
                            f"Fallback provider {name} failed: {fallback_error}"
                        )
                        continue

            # If all providers fail
            raise RuntimeError("All embedding providers failed")

    async def get_embedding(
        self, text: str, provider: Optional[str] = None
    ) -> List[float]:
        """Get embedding for a single text."""
        embeddings = await self.get_embeddings([text], provider)
        return embeddings[0]

    def get_dimension(self, provider: Optional[str] = None) -> int:
        """Get embedding dimension."""
        if provider and provider in self.providers:
            return self.providers[provider].get_dimension()
        return self.primary_provider.get_dimension()

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())

    async def health_check(self) -> dict:
        """Check health of all providers."""
        results = {}
        test_text = "This is a test embedding."

        for name, provider in self.providers.items():
            try:
                await provider.get_embeddings([test_text])
                results[name] = {"status": "healthy", "error": None}
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}

        return results


# Utility functions for vector operations
def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_np = np.array(a)
    b_np = np.array(b)
    return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))


def find_most_similar(
    query_embedding: List[float], candidate_embeddings: List[List[float]]
) -> tuple[int, float]:
    """Find the most similar embedding and its similarity score."""
    similarities = [
        cosine_similarity(query_embedding, candidate)
        for candidate in candidate_embeddings
    ]
    max_idx = np.argmax(similarities)
    return max_idx, similarities[max_idx]


# Global embedding service instance
embedding_service = EmbeddingService()
