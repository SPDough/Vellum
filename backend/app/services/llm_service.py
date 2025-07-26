import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional

import httpx
from anthropic import AsyncAnthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.telemetry import business_metrics, get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer("llm_service")
settings = get_settings()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat_completion(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """Get chat completion from the LLM."""
        pass

    @abstractmethod
    def stream_completion(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from the LLM."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview") -> None:
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

        # Model pricing (per 1K tokens)
        self.pricing = {
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        }

    async def chat_completion(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """Get chat completion from OpenAI."""
        if not self.client:
            raise ValueError("OpenAI API key not provided")

        with tracer.start_as_current_span("openai_chat_completion") as span:
            span.set_attributes(
                {
                    "llm.provider": "openai",
                    "llm.model": self.model,
                    "llm.message_count": len(messages),
                }
            )

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 1000),
                    top_p=kwargs.get("top_p", 1.0),
                    **{
                        k: v
                        for k, v in kwargs.items()
                        if k in ["frequency_penalty", "presence_penalty", "stop"]
                    },
                )

                # Calculate cost
                cost = self._calculate_cost(
                    response.usage.prompt_tokens, response.usage.completion_tokens
                )

                # Record metrics
                business_metrics.record_llm_call(
                    model=self.model,
                    provider="openai",
                    tokens=response.usage.total_tokens,
                    cost=cost,
                )

                span.set_attributes(
                    {
                        "llm.success": True,
                        "llm.tokens_used": response.usage.total_tokens,
                        "llm.cost": cost,
                    }
                )

                return {
                    "content": response.choices[0].message.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    "cost": cost,
                    "model": self.model,
                    "provider": "openai",
                }

            except Exception as e:
                span.set_attribute("llm.success", False)
                span.record_exception(e)
                logger.error(f"OpenAI completion failed: {e}")
                raise

    async def stream_completion(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from OpenAI."""
        if not self.client:
            raise ValueError("OpenAI API key not provided")

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "openai"

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on token usage."""
        pricing = self.pricing.get(self.model, self.pricing["gpt-4-turbo-preview"])
        prompt_cost = (prompt_tokens / 1000) * pricing["input"]
        completion_cost = (completion_tokens / 1000) * pricing["output"]
        return prompt_cost + completion_cost


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229") -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None

        # Model pricing (per 1K tokens)
        self.pricing = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-5-sonnet-20240620": {"input": 0.003, "output": 0.015},
        }

    async def chat_completion(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """Get chat completion from Anthropic."""
        if not self.client:
            raise ValueError("Anthropic API key not provided")

        with tracer.start_as_current_span("anthropic_chat_completion") as span:
            span.set_attributes(
                {
                    "llm.provider": "anthropic",
                    "llm.model": self.model,
                    "llm.message_count": len(messages),
                }
            )

            try:
                # Convert messages to Anthropic format
                anthropic_messages = self._convert_messages(messages)

                response = await self.client.messages.create(
                    model=self.model,
                    messages=anthropic_messages,
                    max_tokens=kwargs.get("max_tokens", 1000),
                    temperature=kwargs.get("temperature", 0.7),
                )

                # Calculate cost
                cost = self._calculate_cost(
                    response.usage.input_tokens, response.usage.output_tokens
                )

                # Record metrics
                business_metrics.record_llm_call(
                    model=self.model,
                    provider="anthropic",
                    tokens=response.usage.input_tokens + response.usage.output_tokens,
                    cost=cost,
                )

                span.set_attributes(
                    {
                        "llm.success": True,
                        "llm.tokens_used": response.usage.input_tokens
                        + response.usage.output_tokens,
                        "llm.cost": cost,
                    }
                )

                return {
                    "content": response.content[0].text,
                    "usage": {
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens
                        + response.usage.output_tokens,
                    },
                    "cost": cost,
                    "model": self.model,
                    "provider": "anthropic",
                }

            except Exception as e:
                span.set_attribute("llm.success", False)
                span.record_exception(e)
                logger.error(f"Anthropic completion failed: {e}")
                raise

    async def stream_completion(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from Anthropic."""
        if not self.client:
            raise ValueError("Anthropic API key not provided")

        anthropic_messages = self._convert_messages(messages)

        async with self.client.messages.stream(
            model=self.model,
            messages=anthropic_messages,
            max_tokens=kwargs.get("max_tokens", 1000),
            temperature=kwargs.get("temperature", 0.7),
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "anthropic"

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert OpenAI-style messages to Anthropic format."""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # Anthropic handles system messages differently
                anthropic_messages.append(
                    {"role": "user", "content": f"System: {msg['content']}"}
                )
            else:
                anthropic_messages.append(msg)
        return anthropic_messages

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        pricing = self.pricing.get(self.model, self.pricing["claude-3-sonnet-20240229"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, base_url: Optional[str] = None, model: str = "llama2") -> None:
        self.base_url = base_url or settings.ollama_base_url
        self.model = model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def chat_completion(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """Get chat completion from Ollama."""
        with tracer.start_as_current_span("ollama_chat_completion") as span:
            span.set_attributes(
                {
                    "llm.provider": "ollama",
                    "llm.model": self.model,
                    "llm.message_count": len(messages),
                }
            )

            try:
                response = await self.client.post(
                    "/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": kwargs.get("temperature", 0.7),
                            "top_p": kwargs.get("top_p", 1.0),
                            "num_predict": kwargs.get("max_tokens", 1000),
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()

                # Estimate tokens (Ollama doesn't provide exact counts)
                estimated_tokens = self._estimate_tokens(
                    messages, result.get("message", {}).get("content", "")
                )

                # Record metrics (no cost for local model)
                business_metrics.record_llm_call(
                    model=self.model,
                    provider="ollama",
                    tokens=estimated_tokens,
                    cost=0.0,
                )

                span.set_attributes(
                    {
                        "llm.success": True,
                        "llm.tokens_used": estimated_tokens,
                        "llm.cost": 0.0,
                    }
                )

                return {
                    "content": result["message"]["content"],
                    "usage": {
                        "prompt_tokens": estimated_tokens // 2,
                        "completion_tokens": estimated_tokens // 2,
                        "total_tokens": estimated_tokens,
                    },
                    "cost": 0.0,
                    "model": self.model,
                    "provider": "ollama",
                }

            except Exception as e:
                span.set_attribute("llm.success", False)
                span.record_exception(e)
                logger.error(f"Ollama completion failed: {e}")
                raise

    def stream_completion(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from Ollama."""
        async def _stream() -> AsyncGenerator[str, None]:
            async with self.client.stream(
                "POST",
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
        
        return _stream()

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "ollama"

    def _estimate_tokens(self, messages: List[Dict[str, str]], response: str) -> int:
        """Estimate token count (rough approximation)."""
        text = " ".join([msg.get("content", "") for msg in messages]) + response
        return int(len(text.split()) * 1.3)  # Rough token estimation


class LLMService:
    """Main LLM service with multiple providers and fallback."""

    def __init__(self) -> None:
        self.providers = self._initialize_providers()
        self.primary_provider = self._get_primary_provider()

    def _initialize_providers(self) -> Dict[str, LLMProvider]:
        """Initialize all available LLM providers."""
        providers: Dict[str, LLMProvider] = {}

        # OpenAI provider
        if settings.openai_api_key:
            try:
                providers["openai"] = OpenAIProvider()
                logger.info("✅ OpenAI LLM provider initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI LLM provider failed: {e}")

        # Anthropic provider
        if settings.anthropic_api_key:
            try:
                providers["anthropic"] = AnthropicProvider()
                logger.info("✅ Anthropic LLM provider initialized")
            except Exception as e:
                logger.warning(f"⚠️ Anthropic LLM provider failed: {e}")

        # Ollama provider (local)
        try:
            providers["ollama"] = OllamaProvider()
            logger.info("✅ Ollama LLM provider initialized")
        except Exception as e:
            logger.warning(f"⚠️ Ollama LLM provider failed: {e}")

        if not providers:
            logger.error("❌ No LLM providers available")
            # Don't raise here, let the service handle gracefully

        return providers

    def _get_primary_provider(self) -> Optional[LLMProvider]:
        """Get the primary provider based on preferences."""
        # Preference order: OpenAI -> Anthropic -> Ollama
        for provider_name in ["openai", "anthropic", "ollama"]:
            if provider_name in self.providers:
                logger.info(f"Using {provider_name} as primary LLM provider")
                return self.providers[provider_name]

        logger.warning("No primary LLM provider available")
        return None

    async def chat_completion(
        self, messages: List[Dict[str, str]], provider: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Get chat completion with automatic fallback."""
        # Choose provider
        if provider and provider in self.providers:
            chosen_provider = self.providers[provider]
        elif self.primary_provider:
            chosen_provider = self.primary_provider
        else:
            raise RuntimeError("No LLM providers available")

        # Try primary provider first
        try:
            return await chosen_provider.chat_completion(messages, **kwargs)
        except Exception as e:
            logger.warning(f"Primary LLM provider failed: {e}, trying fallbacks...")

            # Try other providers as fallback
            for name, fallback_provider in self.providers.items():
                if fallback_provider != chosen_provider:
                    try:
                        logger.info(f"Trying fallback LLM provider: {name}")
                        return await fallback_provider.chat_completion(
                            messages, **kwargs
                        )
                    except Exception as fallback_error:
                        logger.warning(
                            f"Fallback LLM provider {name} failed: {fallback_error}"
                        )
                        continue

            # If all providers fail
            raise RuntimeError("All LLM providers failed")

    def stream_completion(
        self, messages: List[Dict[str, str]], provider: Optional[str] = None, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        # Choose provider
        if provider and provider in self.providers:
            chosen_provider = self.providers[provider]
        elif self.primary_provider:
            chosen_provider = self.primary_provider
        else:
            raise RuntimeError("No LLM providers available")

        return chosen_provider.stream_completion(messages, **kwargs)

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers."""
        results = {}
        test_messages = [{"role": "user", "content": "Hello, this is a test."}]

        for name, provider in self.providers.items():
            try:
                response = await provider.chat_completion(test_messages, max_tokens=10)
                results[name] = {
                    "status": "healthy",
                    "model": provider.get_model_name(),
                    "error": None,
                }
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "model": provider.get_model_name(),
                    "error": str(e),
                }

        return results


# Global LLM service instance
llm_service = LLMService()
