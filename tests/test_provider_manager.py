"""Tests for ProviderManager routing, error classification, and fallback policies."""

import pytest
from unittest.mock import MagicMock
from storybook.providers.provider_manager import ProviderManager, ProviderExecutionResult
from storybook.config import config


def test_provider_manager_default_routing():
    """Verify ProviderManager routes to MockProvider when configured."""
    pm = ProviderManager()
    p = pm.get_provider("mock")
    assert p.get_provider_name() == "mock"


def test_temporary_error_classification():
    """Verify is_temporary_error correctly identifies 429, timeouts, and rate limits."""
    pm = ProviderManager()
    assert pm.is_temporary_error(RuntimeError("429 Too Many Requests")) is True
    assert pm.is_temporary_error(RuntimeError("Rate limit exceeded")) is True
    assert pm.is_temporary_error(RuntimeError("503 Service Unavailable")) is True
    assert pm.is_temporary_error(RuntimeError("Connection timed out")) is True
    assert pm.is_temporary_error(ValueError("Invalid API key provided")) is False
    assert pm.is_temporary_error(ValueError("Field required: title")) is False


def test_execution_with_mock_provider():
    """Verify successful execution records provider name and fallback=False."""
    pm = ProviderManager()
    res = pm.execute_with_fallback(
        operation_name="test_op",
        func=lambda p: p.generate_text("Hi"),
        preferred_provider="mock",
    )
    assert isinstance(res, ProviderExecutionResult)
    assert res.provider_name == "mock"
    assert res.fallback_used is False
    assert "[Mock Provider Output]" in res.data


def test_disabled_fallback_raises_immediately():
    """Verify that when fallback is disabled, primary failure raises directly."""
    pm = ProviderManager()
    # Mock primary provider that fails with 429
    failing_provider = MagicMock()
    failing_provider.generate_text.side_effect = RuntimeError("429 Rate limit")

    pm.get_provider = MagicMock(return_value=failing_provider)

    original_setting = config.ai_auto_fallback
    config.ai_auto_fallback = False
    try:
        with pytest.raises(RuntimeError) as exc:
            pm.execute_with_fallback(
                operation_name="test_op",
                func=lambda p: p.generate_text("Hi"),
                preferred_provider="gemini",
            )
        assert "429 Rate limit" in str(exc.value)
    finally:
        config.ai_auto_fallback = original_setting
