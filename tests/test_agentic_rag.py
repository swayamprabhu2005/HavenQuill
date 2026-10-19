"""Automated unit tests for Agentic RAG Rolling Memory Service and Story Segments."""

import pytest
from storybook.database import DatabaseManager
from storybook.models import StorySegment, Project, CanonFact, Character
from storybook.repositories import (
    ProjectRepository,
    StorySegmentRepository,
    StoryBibleRepository,
    ChapterRepository,
    SceneRepository,
    VersionHistoryRepository,
)
from storybook.services.agentic_rag_service import AgenticRAGService


@pytest.fixture
def rag_service(test_db: DatabaseManager) -> AgenticRAGService:
    return AgenticRAGService(
        segment_repo=StorySegmentRepository(test_db),
        project_repo=ProjectRepository(test_db),
        chapter_repo=ChapterRepository(test_db),
        scene_repo=SceneRepository(test_db),
        bible_repo=StoryBibleRepository(test_db),
        version_repo=VersionHistoryRepository(test_db),
    )


@pytest.fixture
def sample_project_id(test_db: DatabaseManager) -> str:
    proj_repo = ProjectRepository(test_db)
    proj = proj_repo.create(
        Project(
            title="The Silver Archives",
            genre="Fantasy",
            tone="Mysterious",
            premise="A scholar unravels subterranean ancient knowledge.",
        )
    )
    return proj.id


def test_story_segment_crud(test_db: DatabaseManager, sample_project_id: str):
    repo = StorySegmentRepository(test_db)

    # 1. Create segments
    seg1 = repo.create(
        StorySegment(
            project_id=sample_project_id,
            segment_index=1,
            raw_input="Elena reached the forgotten library under the hollow mountain.",
            status="pending",
            word_count=10,
        )
    )
    assert seg1.id is not None
    assert seg1.segment_index == 1
    assert seg1.status == "pending"

    seg2 = repo.create(
        StorySegment(
            project_id=sample_project_id,
            segment_index=2,
            raw_input="The silver doors opened with a deep vibration echoing in the chamber.",
            status="pending",
            word_count=12,
        )
    )
    assert seg2.id is not None

    # 2. List ordered
    segments = repo.list_by_project(sample_project_id)
    assert len(segments) == 2
    assert segments[0].segment_index == 1
    assert segments[1].segment_index == 2

    # 3. Update segment (commit with generated prose)
    seg1.status = "processed"
    seg1.generated_prose = "Deep beneath the peaks, Elena discovered the ancient threshold."
    updated = repo.update(seg1)
    assert updated.status == "processed"
    assert "Elena discovered" in updated.generated_prose


def test_keyword_boundary_detection(rag_service: AgenticRAGService):
    # Test valid boundary markers
    has_b1, clean1 = rag_service.check_keyword_boundary("The sun began to set behind the ridge. Para one end.")
    assert has_b1 is True
    assert "behind the ridge." in clean1

    has_b2, clean2 = rag_service.check_keyword_boundary("And so she took her first step forward. Paragraph end")
    assert has_b2 is True
    assert "took her first step forward." in clean2

    has_b3, clean3 = rag_service.check_keyword_boundary("A gentle breeze ruffled the old pages. End of para.")
    assert has_b3 is True
    assert "ruffled the old pages." in clean3

    # Test text without boundary markers
    has_b4, clean4 = rag_service.check_keyword_boundary("Elena paused and listened carefully for any sound.")
    assert has_b4 is False
    assert clean4 == "Elena paused and listened carefully for any sound."


def test_agentic_context_packet_assembly(test_db: DatabaseManager, rag_service: AgenticRAGService, sample_project_id: str):
    seg_repo = StorySegmentRepository(test_db)
    bible_repo = StoryBibleRepository(test_db)

    # Add characters and world canon
    char = Character(
        project_id=sample_project_id,
        canonical_name="Elena Ward",
        aliases_json=["Elena"],
        traits_json=["Brave cartographer", "Sharp eye"],
        description="A courageous cartographer exploring the hollow mountain.",
    )
    bible_repo.create_character(char)

    fact = CanonFact(
        project_id=sample_project_id,
        fact_text="Silver Mist produces a soft blue glow at twilight and causes disorientation.",
        category="world_rule",
        is_locked=True,
    )
    bible_repo.create_canon_fact(fact)

    # Add a committed previous segment (long enough to demonstrate token/word savings)
    seg_repo.create(
        StorySegment(
            project_id=sample_project_id,
            segment_index=1,
            raw_input="Elena stepped through the subterranean mist cautiously, observing each ancient pillar. " * 20,
            generated_prose="Elena cautiously stepped through the luminescent silver mist. Her compass needle trembled erratically.",
            status="processed",
            word_count=200,
        )
    )

    # Active segment
    active_seg = StorySegment(
        project_id=sample_project_id,
        segment_index=2,
        raw_input="She saw shadows moving between the pillars.",
        status="pending",
        word_count=7,
    )

    # Build context packet
    context = rag_service.build_agentic_rag_context(sample_project_id, active_seg)
    assert context["project_title"] == "The Silver Archives"
    assert any("Elena Ward" in c for c in context["characters"])
    assert any("Silver Mist" in f for f in context["locked_facts"])
    assert "Her compass needle trembled erratically." in context["bridge_sentence"]
    assert len(context["rolling_recap"]) == 1
    assert context["estimated_words_saved"] > 0


def test_segment_transformation_and_token_savings(
    test_db: DatabaseManager, rag_service: AgenticRAGService, sample_project_id: str
):
    seg_repo = StorySegmentRepository(test_db)

    # Create pending segment
    seg = seg_repo.create(
        StorySegment(
            project_id=sample_project_id,
            segment_index=1,
            raw_input="She noticed strange runes glowing on the floor stones. They smelled faintly of ozone and old parchment.",
            status="pending",
            word_count=18,
        )
    )

    # Transform segment with Mock provider (works without keys)
    result = rag_service.process_segment_with_ai(
        project_id=sample_project_id,
        segment_id=seg.id,
        preferred_provider="mock",
    )

    assert result.data is not None
    assert result.provider_name == "mock"
    updated_seg = seg_repo.get(seg.id)
    assert updated_seg.status == "processed"
    assert updated_seg.generated_prose is not None
    assert len(updated_seg.generated_prose) > 0


def test_segment_rethink_without_touching_history(
    test_db: DatabaseManager, rag_service: AgenticRAGService, sample_project_id: str
):
    seg_repo = StorySegmentRepository(test_db)

    # Create segment 1 committed
    seg1 = seg_repo.create(
        StorySegment(
            project_id=sample_project_id,
            segment_index=1,
            raw_input="Elena found the bronze chest.",
            generated_prose="Elena knelt beside the centuries-old bronze chest.",
            status="processed",
            word_count=5,
        )
    )

    # Create segment 2 committed
    seg2 = seg_repo.create(
        StorySegment(
            project_id=sample_project_id,
            segment_index=2,
            raw_input="The lock gave way with a click.",
            generated_prose="The heavy lock clicked open.",
            status="processed",
            word_count=7,
        )
    )

    original_seg1_prose = seg1.generated_prose

    # Rethink segment 2 with custom instruction
    result = rag_service.rethink_segment(
        project_id=sample_project_id,
        segment_id=seg2.id,
        feedback="Add more suspense and sensory tension regarding the clicking mechanism.",
        preferred_provider="mock",
    )

    assert result.data is not None
    assert result.provider_name == "mock"
    # Segment 1 must remain completely untouched
    refreshed_seg1 = seg_repo.get(seg1.id)
    assert refreshed_seg1.generated_prose == original_seg1_prose

    # Segment 2 has updated prose
    refreshed_seg2 = seg_repo.get(seg2.id)
    assert refreshed_seg2.generated_prose is not None
