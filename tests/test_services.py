"""Comprehensive service-layer tests using MockProvider."""

import pytest
from storybook.models import Project


def test_story_service_workflow(services):
    """Test full story development workflow with MockProvider."""
    s_srv = services["story"]

    # 1. Create project
    proj = s_srv.create_project(
        title="Chronicles of the Clocksmith",
        genre="Steampunk",
        tone="Atmospheric",
        premise="An outcast smith discovers a chronometer that records lost history.",
    )
    assert proj.id is not None

    # 2. Save source draft
    draft = s_srv.save_source_draft(
        project_id=proj.id,
        source_type="typed",
        original_text="Rough notes: Clocksmith meets archivist in Vault B.",
    )
    assert draft.id is not None
    drafts = s_srv.list_source_drafts(proj.id)
    assert len(drafts) == 1

    # 3. Develop story
    res = s_srv.develop_story(proj.id, preferred_provider="mock")
    assert res.provider_name == "mock"
    updated_proj = s_srv.get_project(proj.id)
    assert "story_development" in updated_proj.metadata_json


def test_outline_and_chapter_service(services):
    """Test outline proposal generation and chapter creation."""
    s_srv = services["story"]
    o_srv = services["outline"]

    proj = s_srv.create_project(
        title="Outline Test Project",
        premise="A mystery in a subterranean city.",
    )

    # Generate outline proposal
    prop_res = o_srv.generate_outline_proposal(proj.id, num_chapters=4, preferred_provider="mock")
    outline = prop_res.data
    assert len(outline.chapters) == 4

    # Apply outline
    created_chapters = o_srv.apply_outline_to_project(proj.id, outline, overwrite_existing=False)
    assert len(created_chapters) == 4

    # Reorder
    ch_ids = [c.id for c in created_chapters]
    reversed_ids = list(reversed(ch_ids))
    o_srv.reorder_chapters(proj.id, reversed_ids)

    reordered = o_srv.list_chapters(proj.id)
    assert reordered[0].id == reversed_ids[0]


def test_scene_lifecycle_and_operations(services):
    """Test scene creation, breakdown, movement, splitting, merging, and prose drafting."""
    s_srv = services["story"]
    o_srv = services["outline"]
    sc_srv = services["scene"]

    proj = s_srv.create_project(title="Scene Test", premise="Testing scenes")
    ch = o_srv.create_chapter(proj.id, title="Chapter 1")

    # Generate breakdown
    bd_res = sc_srv.generate_scene_breakdown_proposal(ch.id, num_scenes=3, preferred_provider="mock")
    scenes = sc_srv.apply_scenes_to_chapter(ch.id, bd_res.data, overwrite_existing=True)
    assert len(scenes) == 3

    sc1, sc2, sc3 = scenes[0], scenes[1], scenes[2]

    # Move scene down
    move_ok = sc_srv.move_scene(sc1.id, "down")
    assert move_ok is True
    reordered_scenes = sc_srv.list_scenes_by_chapter(ch.id)
    assert reordered_scenes[0].id == sc2.id
    assert reordered_scenes[1].id == sc1.id

    # Draft prose
    sc_srv.draft_scene_prose(sc1.id, preferred_provider="mock")
    drafted_sc = sc_srv.get_scene(sc1.id)
    assert drafted_sc.prose is not None
    assert len(drafted_sc.prose) > 20

    # Duplicate scene
    dup_sc = sc_srv.duplicate_scene(sc1.id)
    assert dup_sc.title.endswith("(Copy)")
    assert len(sc_srv.list_scenes_by_chapter(ch.id)) == 4

    # Split scene
    part1, part2 = sc_srv.split_scene(sc1.id, split_char_index=30, second_title="Split Part 2")
    assert part2.title == "Split Part 2"

    # Merge scenes
    merged = sc_srv.merge_scenes(sc1.id, part2.id)
    assert sc_srv.get_scene(part2.id) is None


def test_story_bible_and_canon_locking(services):
    """Test story bible entities, locked canon facts, and contradiction detection."""
    s_srv = services["story"]
    b_srv = services["bible"]

    proj = s_srv.create_project(title="Canon Test", premise="Testing canon locking")

    # Create character
    char = b_srv.create_character(
        project_id=proj.id,
        name="Elena Vance",
        traits=["Brave", "Perceptive"],
    )
    assert char.canonical_name == "Elena Vance"

    # Create locked canon fact
    fact = b_srv.create_canon_fact(
        project_id=proj.id,
        fact_text="The Great Erasure happened in 1842 and cannot be undone.",
        category="world",
        subject="The Great Erasure",
        is_locked=True,
    )
    assert fact.is_locked is True

    # Test contradiction checking
    warnings = b_srv.check_for_canon_contradictions(
        project_id=proj.id,
        candidate_text="In this scene, the author rewrites The Great Erasure event.",
    )
    assert len(warnings) == 1
    assert "The Great Erasure" in warnings[0]


def test_continuity_audit_service(services):
    """Test continuity audit service over canon facts and scene progression."""
    s_srv = services["story"]
    o_srv = services["outline"]
    sc_srv = services["scene"]
    b_srv = services["bible"]
    c_srv = services["continuity"]

    proj = s_srv.create_project(title="Audit Test", premise="Testing continuity review")
    b_srv.create_canon_fact(proj.id, "Magic does not exist.", is_locked=True)
    ch = o_srv.create_chapter(proj.id, "Ch 1")
    sc_srv.create_scene(ch.id, "Scene 1", summary="Elena studies books in the quiet library.")

    res = c_srv.audit_project_continuity(proj.id, preferred_provider="mock")
    assert res.provider_name == "mock"
    audit = res.data
    assert audit.consistency_score > 0
