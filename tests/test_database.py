"""Tests for SQLite database operations, project isolation, and schema integrity."""

import pytest
from storybook.models import Project, SourceDraft, Chapter, Scene, Character, CanonFact


def test_database_initialization(test_db):
    """Verify database initializes tables, indexes, and schema version."""
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT version FROM schema_version")
        ver = cur.fetchone()[0]
        assert ver >= 1

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        assert "projects" in tables
        assert "source_drafts" in tables
        assert "chapters" in tables
        assert "scenes" in tables
        assert "characters" in tables
        assert "locations" in tables
        assert "canon_facts" in tables
        assert "story_events" in tables
        assert "version_history" in tables
        assert "ai_jobs" in tables


def test_project_crud(repos):
    """Test Project creation, retrieval, updating, and deletion."""
    project_repo = repos["project"]

    p = Project(
        title="The Glass Citadel",
        subtitle="Chronicles of Aerith",
        genre="High Fantasy",
        tone="Epic",
        premise="A kingdom made of diamond collapses under the weight of a forgotten spell.",
    )
    saved = project_repo.create(p)
    assert saved.id == p.id

    fetched = project_repo.get(saved.id)
    assert fetched is not None
    assert fetched.title == "The Glass Citadel"
    assert fetched.genre == "High Fantasy"

    fetched.title = "The Obsidian Citadel"
    updated = project_repo.update(fetched)
    assert updated.title == "The Obsidian Citadel"

    del_res = project_repo.delete(saved.id)
    assert del_res is True
    assert project_repo.get(saved.id) is None


def test_project_isolation(repos):
    """Verify that multiple projects maintain strictly isolated data."""
    p_repo = repos["project"]
    ch_repo = repos["chapter"]
    sc_repo = repos["scene"]
    b_repo = repos["bible"]

    p1 = p_repo.create(Project(title="Project Alpha", premise="Premise 1"))
    p2 = p_repo.create(Project(title="Project Beta", premise="Premise 2"))

    # Chapters in P1
    c1 = ch_repo.create(Chapter(project_id=p1.id, order_index=1, title="Alpha Ch 1"))
    # Chapters in P2
    c2 = ch_repo.create(Chapter(project_id=p2.id, order_index=1, title="Beta Ch 1"))

    # Verify chapters isolated
    p1_chapters = ch_repo.list_by_project(p1.id)
    p2_chapters = ch_repo.list_by_project(p2.id)

    assert len(p1_chapters) == 1
    assert p1_chapters[0].title == "Alpha Ch 1"
    assert len(p2_chapters) == 1
    assert p2_chapters[0].title == "Beta Ch 1"

    # Characters in P1 vs P2
    b_repo.create_character(Character(project_id=p1.id, canonical_name="Alice"))
    b_repo.create_character(Character(project_id=p2.id, canonical_name="Bob"))

    assert [c.canonical_name for c in b_repo.list_characters(p1.id)] == ["Alice"]
    assert [c.canonical_name for c in b_repo.list_characters(p2.id)] == ["Bob"]


def test_cascading_deletes(repos):
    """Verify that deleting a project cascades to delete chapters, scenes, characters, and drafts."""
    p_repo = repos["project"]
    d_repo = repos["draft"]
    ch_repo = repos["chapter"]
    sc_repo = repos["scene"]
    b_repo = repos["bible"]

    p = p_repo.create(Project(title="Temporary Project", premise="To be deleted"))
    ch = ch_repo.create(Chapter(project_id=p.id, order_index=1, title="Chapter 1"))
    sc = sc_repo.create(Scene(chapter_id=ch.id, order_index=1, title="Scene 1"))
    d = d_repo.create(SourceDraft(project_id=p.id, source_type="typed", original_text="Raw notes"))
    char = b_repo.create_character(Character(project_id=p.id, canonical_name="Temp Character"))

    # Delete project
    p_repo.delete(p.id)

    # Verify cascades
    assert ch_repo.get(ch.id) is None
    assert sc_repo.get(sc.id) is None
    assert d_repo.get(d.id) is None
    assert len(b_repo.list_characters(p.id)) == 0


def test_chapter_and_scene_reordering(repos):
    """Test reordering of chapters and scenes."""
    p_repo = repos["project"]
    ch_repo = repos["chapter"]
    sc_repo = repos["scene"]

    p = p_repo.create(Project(title="Order Test", premise="Ordering test"))
    ch1 = ch_repo.create(Chapter(project_id=p.id, order_index=1, title="Ch 1"))
    ch2 = ch_repo.create(Chapter(project_id=p.id, order_index=2, title="Ch 2"))

    sc1 = sc_repo.create(Scene(chapter_id=ch1.id, order_index=1, title="Scene 1"))
    sc2 = sc_repo.create(Scene(chapter_id=ch1.id, order_index=2, title="Scene 2"))

    # Reorder scenes
    sc_repo.reorder(ch1.id, [sc2.id, sc1.id])
    reordered_scenes = sc_repo.list_by_chapter(ch1.id)
    assert reordered_scenes[0].id == sc2.id
    assert reordered_scenes[0].order_index == 1
    assert reordered_scenes[1].id == sc1.id
    assert reordered_scenes[1].order_index == 2


def test_version_history_recording(repos):
    """Verify version history snapshots are stored and retrieved."""
    vh_repo = repos["version"]
    p_repo = repos["project"]

    p = p_repo.create(Project(title="Versioned Story", premise="Testing snapshots"))
    snap1 = vh_repo.record_snapshot(
        entity_type="project",
        entity_id=p.id,
        snapshot=p.model_dump(),
        reason="Initial creation",
    )

    history = vh_repo.get_history(entity_type="project", entity_id=p.id)
    assert len(history) == 1
    assert history[0].reason == "Initial creation"
    assert history[0].content_snapshot_json["title"] == "Versioned Story"
