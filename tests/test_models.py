"""Tests for Pydantic models, structured outputs, and future image schema compatibility."""

import pytest
from pydantic import ValidationError
from storybook.models import (
    StoryDevelopmentResponse,
    OutlineResponse,
    OutlineChapterProposal,
    SceneBreakdownResponse,
    SceneProposal,
    StoryBibleExtractionResponse,
    ContinuityReviewResponse,
    ContinuityIssue,
    Scene,
)


def test_story_development_response_valid():
    """Verify StoryDevelopmentResponse parses structured story data."""
    data = {
        "logline": "A rogue astronaut must navigate a sentient wormhole to return home.",
        "short_synopsis": "Captain Miller discovers the wormhole responds to emotional states.",
        "detailed_synopsis": "Act I introduces Miller. Act II tests his resolve. Act III concludes with transcendence.",
        "themes": ["Grief", "Exploration", "Identity"],
        "main_conflict": "Survival versus the loss of humanity.",
        "main_character_goals": ["Return to Earth", "Understand the anomaly"],
        "major_turning_points": ["First contact with the singularity", "Oxygen failure"],
        "proposed_ending": "Miller escapes by accepting his past.",
        "open_questions": ["What is the origin of the entity?"],
        "assumptions": ["Hard sci-fi physics rules apply until crossing the event horizon."],
    }
    model = StoryDevelopmentResponse.model_validate(data)
    assert model.logline == data["logline"]
    assert len(model.themes) == 3


def test_story_development_response_missing_required():
    """Verify ValidationError is raised when required fields are omitted."""
    with pytest.raises(ValidationError):
        StoryDevelopmentResponse.model_validate({"logline": "Just a logline"})


def test_scene_proposal_future_image_compatibility():
    """Verify Scene and SceneProposal preserve future image and visual framing metadata."""
    scene_prop = SceneProposal(
        order_index=1,
        title="The Confrontation at the Pier",
        summary="Elena confronts Silas at the dock edge.",
        purpose="Introduce dramatic friction.",
        pov="Elena Vance",
        location="Pier 4",
        time_marker="Dusk",
        characters_present=["Elena Vance", "Silas Rook"],
        dramatic_conflict="Silas refuses to surrender the cipher.",
        emotional_shift="Suspicion turns to reluctant alliance.",
        camera_framing="Low-angle two-shot framing both figures against the burning horizon.",
        mood_atmosphere="Melancholy, amber dusk lighting, harsh silhouettes.",
        visual_summary="A woman in dark trench coat facing a broad-shouldered smith with glowing welding goggles.",
    )

    assert scene_prop.camera_framing.startswith("Low-angle")
    assert "Elena Vance" in scene_prop.characters_present
    assert scene_prop.visual_summary is not None

    # Test database Scene model compatibility
    db_scene = Scene(
        chapter_id="test-ch",
        order_index=1,
        title=scene_prop.title,
        summary=scene_prop.summary,
        camera_framing=scene_prop.camera_framing,
        mood_atmosphere=scene_prop.mood_atmosphere,
        visual_summary=scene_prop.visual_summary,
        characters_present=scene_prop.characters_present,
    )
    assert db_scene.camera_framing == scene_prop.camera_framing
    assert db_scene.mood_atmosphere == scene_prop.mood_atmosphere


def test_continuity_review_response():
    """Verify ContinuityReviewResponse parses issues and scores."""
    data = {
        "summary": "Audited 5 chapters; 1 discrepancy found.",
        "consistency_score": 90,
        "issues": [
            {
                "category": "timeline_conflict",
                "severity": "high",
                "description": "Character arrives before train departs.",
                "related_entities": ["Elena", "The 4 PM Express"],
                "suggested_fix": "Change arrival time to 3:30 PM.",
            }
        ],
    }
    review = ContinuityReviewResponse.model_validate(data)
    assert review.consistency_score == 90
    assert len(review.issues) == 1
    assert review.issues[0].severity == "high"
