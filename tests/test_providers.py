"""Tests for Mock, Gemini, and Groq AI providers."""

import pytest
from storybook.providers.mock_provider import MockProvider
from storybook.providers.gemini_provider import GeminiProvider
from storybook.providers.groq_provider import GroqProvider
from storybook.models import (
    StoryDevelopmentResponse,
    OutlineResponse,
    SceneBreakdownResponse,
    StoryBibleExtractionResponse,
    ContinuityReviewResponse,
    SceneRewriteResponse,
)


def test_mock_provider_full_workflow():
    """Verify MockProvider produces valid deterministic schema outputs completely offline."""
    mock = MockProvider()

    # Connection test
    conn = mock.test_connection()
    assert conn["ok"] is True
    assert conn["provider"] == "mock"

    # Text generation
    text = mock.generate_text("Write a scene")
    assert "[Mock Provider Output]" in text

    # Story development
    dev = mock.generate_story_development(
        premise="A clockmaker finds lost time",
        genre="Steampunk",
        tone="Dark",
        audience="Adult",
        notes="None",
    )
    assert isinstance(dev, StoryDevelopmentResponse)
    assert len(dev.themes) > 0
    assert dev.logline is not None

    # Outline
    outline = mock.generate_outline("Premise", "Synopsis", num_chapters=3)
    assert isinstance(outline, OutlineResponse)
    assert len(outline.chapters) == 3

    # Scene breakdown
    breakdown = mock.generate_scene_breakdown("Chapter 1", "Summary", num_scenes=2)
    assert isinstance(breakdown, SceneBreakdownResponse)
    assert len(breakdown.scenes) == 2

    # Prose drafting
    prose = mock.draft_scene_prose(breakdown.scenes[0], context="Context")
    assert "Mock Generated Prose" in prose

    # Rewrite
    rewrite = mock.rewrite_scene(prose, instructions="Tighten dialogue")
    assert isinstance(rewrite, SceneRewriteResponse)
    assert rewrite.rewritten_prose is not None

    # Story Bible extraction
    bible = mock.extract_story_bible("Some manuscript text")
    assert isinstance(bible, StoryBibleExtractionResponse)
    assert len(bible.characters) >= 2

    # Continuity review
    review = mock.review_continuity(["Fact 1"], ["Scene 1"])
    assert isinstance(review, ContinuityReviewResponse)
    assert review.consistency_score > 0


def test_gemini_missing_key_handling():
    """Verify GeminiProvider raises clear ValueError when API key is missing."""
    gemini = GeminiProvider(api_key="", model_name="gemini-2.5-flash")

    test_res = gemini.test_connection()
    assert test_res["ok"] is False
    assert "not configured" in test_res["message"].lower()

    with pytest.raises(ValueError) as excinfo:
        gemini.generate_text("Hello")
    assert "API key is not configured" in str(excinfo.value)


def test_groq_missing_key_handling():
    """Verify GroqProvider raises clear ValueError when API key is missing."""
    groq = GroqProvider(api_key="", model_name="llama-3.3-70b-versatile")

    test_res = groq.test_connection()
    assert test_res["ok"] is False
    assert "not configured" in test_res["message"].lower()

    with pytest.raises(ValueError) as excinfo:
        groq.generate_text("Hello")
    assert "API key is not configured" in str(excinfo.value)


def test_provider_malformed_response_handling():
    """Verify that malformed JSON returned by providers triggers clean ValueError."""
    from unittest.mock import MagicMock
    gemini = GeminiProvider(api_key="mock_key", model_name="gemini-2.5-flash")
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "{ this is not valid json! }"
    mock_client.models.generate_content.return_value = mock_resp
    gemini._client = mock_client

    with pytest.raises(ValueError) as exc:
        gemini._generate_structured("prompt", StoryDevelopmentResponse)
    assert "expected structure" in str(exc.value).lower()

