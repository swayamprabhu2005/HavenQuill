"""Provider Manager handling provider routing, fallback policies, and execution telemetry."""

import logging
from typing import Optional, List, Dict, Any, Callable, TypeVar
from pydantic import BaseModel

from storybook.config import config
from storybook.providers.base import BaseAIProvider
from storybook.providers.mock_provider import MockProvider
from storybook.providers.gemini_provider import GeminiProvider
from storybook.providers.groq_provider import GroqProvider

logger = logging.getLogger(__name__)
T = TypeVar("T")


class ProviderExecutionResult:
    """Encapsulates the result of an AI operation along with provider telemetry."""

    def __init__(self, data: Any, provider_name: str, model_name: str, fallback_used: bool = False, notes: str = ""):
        self.data = data
        self.provider_name = provider_name
        self.model_name = model_name
        self.fallback_used = fallback_used
        self.notes = notes

    def __repr__(self) -> str:
        return f"<ProviderExecutionResult provider={self.provider_name} fallback={self.fallback_used}>"


class ProviderManager:
    """Coordinates active provider selection and configurable fallback logic."""

    def __init__(self):
        self._mock = MockProvider()

    def get_provider(self, provider_name: Optional[str] = None) -> BaseAIProvider:
        """Instantiate the requested provider or the configured default."""
        target = (provider_name or config.ai_provider or "mock").lower().strip()

        if target == "gemini":
            return GeminiProvider(api_key=config.gemini_api_key, model_name=config.gemini_model)
        elif target == "groq":
            return GroqProvider(api_key=config.groq_api_key, model_name=config.groq_model)
        elif target == "mock":
            return self._mock
        else:
            logger.warning(f"Unknown provider '{target}', defaulting to MockProvider.")
            return self._mock

    def test_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """Run connectivity checks across all three providers."""
        results = {}
        # Mock
        results["mock"] = self._mock.test_connection()
        # Gemini
        gemini = GeminiProvider(api_key=config.gemini_api_key, model_name=config.gemini_model)
        results["gemini"] = gemini.test_connection()
        # Groq
        groq = GroqProvider(api_key=config.groq_api_key, model_name=config.groq_model)
        results["groq"] = groq.test_connection()

        return results

    def is_temporary_error(self, error: Exception) -> bool:
        """Determine if an error is temporary (rate limit, quota, server unavailable, timeout)."""
        msg = str(error).lower()
        temporary_keywords = [
            "429", "rate limit", "quota", "resource exhausted", "too many requests",
            "503", "500", "502", "service unavailable", "timeout", "timed out",
            "overloaded", "server error"
        ]
        return any(keyword in msg for keyword in temporary_keywords)

    def execute_with_fallback(
        self,
        operation_name: str,
        func: Callable[[BaseAIProvider], T],
        preferred_provider: Optional[str] = None,
    ) -> ProviderExecutionResult:
        """
        Execute an AI operation with the configured provider.
        If the primary provider encounters a temporary failure and AI_AUTO_FALLBACK is enabled,
        attempt execution using the fallback provider (Groq) if configured.
        """
        active_name = (preferred_provider or config.ai_provider or "mock").lower()
        primary_provider = self.get_provider(active_name)

        try:
            result = func(primary_provider)
            return ProviderExecutionResult(
                data=result,
                provider_name=primary_provider.get_provider_name(),
                model_name=primary_provider.get_model_name(),
                fallback_used=False,
            )
        except Exception as primary_error:
            # Check if fallback is appropriate
            can_fallback = (
                config.ai_auto_fallback
                and active_name == "gemini"
                and config.is_groq_configured
                and self.is_temporary_error(primary_error)
            )

            if not can_fallback:
                logger.error(
                    f"AI operation '{operation_name}' failed on {active_name}: {primary_error}"
                )
                raise primary_error

            # Attempt fallback to Groq
            logger.warning(
                f"Primary provider {active_name} failed with temporary error ({primary_error}). "
                "Attempting automatic fallback to Groq..."
            )

            fallback_provider = self.get_provider("groq")
            try:
                result = func(fallback_provider)
                return ProviderExecutionResult(
                    data=result,
                    provider_name=fallback_provider.get_provider_name(),
                    model_name=fallback_provider.get_model_name(),
                    fallback_used=True,
                    notes=f"Primary ({active_name}) experienced temporary disruption; successfully completed with Groq.",
                )
            except Exception as fallback_error:
                logger.error(f"Fallback to Groq also failed: {fallback_error}")
                raise RuntimeError(
                    f"Primary provider ({active_name}) failed: {primary_error}. "
                    f"Fallback provider (groq) also failed: {fallback_error}"
                ) from fallback_error


# Singleton instance
provider_manager = ProviderManager()
