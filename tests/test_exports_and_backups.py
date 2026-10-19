"""Tests for exports (PDF, Markdown, JSON, DOCX), backup ZIPs, secret exclusion, and restore."""

import json
import pytest
from storybook.models import Project, Chapter, Scene, Character, CanonFact


def test_markdown_export(services):
    """Verify Markdown manuscript export format and contents."""
    s_srv = services["story"]
    o_srv = services["outline"]
    sc_srv = services["scene"]
    exp_srv = services["export"]

    proj = s_srv.create_project(title="The Clockwork Tale", subtitle="A Short Novel", premise="Clockwork story")
    ch1 = o_srv.create_chapter(proj.id, "The First Gear", summary="Elena discovers the gear.")
    sc_srv.create_scene(ch1.id, "The Discovery", prose="Elena picked up the gear. It was cold to the touch.")

    md = exp_srv.export_markdown(proj.id)
    assert "# The Clockwork Tale" in md
    assert "## The First Gear" in md
    assert "### The Discovery" in md
    assert "Elena picked up the gear." in md


def test_json_export_and_future_image_schema(services):
    """Verify JSON export contains stable IDs, future visual metadata, and no secrets."""
    s_srv = services["story"]
    o_srv = services["outline"]
    sc_srv = services["scene"]
    b_srv = services["bible"]
    exp_srv = services["export"]

    proj = s_srv.create_project(title="JSON Test", premise="Testing JSON export")
    ch = o_srv.create_chapter(proj.id, "Ch 1")
    sc = sc_srv.create_scene(
        ch.id,
        "Scene 1",
        prose="Prose here",
        characters_present=["Elena", "Silas"],
    )
    b_srv.create_character(proj.id, "Elena Vance")
    b_srv.create_canon_fact(proj.id, "Fact text", is_locked=True)

    data = exp_srv.export_json(proj.id)
    assert data["schema_version"] == "1.0.0"
    assert data["project"]["id"] == proj.id
    assert len(data["chapters"]) == 1
    assert len(data["chapters"][0]["scenes"]) == 1

    scene_data = data["chapters"][0]["scenes"][0]
    # Check future image / comic schema fields
    assert "visual_metadata" in scene_data
    assert "camera_framing" in scene_data["visual_metadata"]
    assert "character_visual_refs" in scene_data["visual_metadata"]
    assert scene_data["visual_metadata"]["character_visual_refs"] == ["Elena", "Silas"]

    # Secret exclusion verification
    serialized = json.dumps(data).lower()
    for secret in ["api_key", "secret", "password", "token", "aiza", "gsk_"]:
        assert secret not in serialized


def test_pdf_export_reportlab(services):
    """Verify ReportLab produces valid PDF bytes."""
    s_srv = services["story"]
    o_srv = services["outline"]
    sc_srv = services["scene"]
    exp_srv = services["export"]

    proj = s_srv.create_project(title="PDF Test Story", subtitle="Illustrated Edition", premise="Testing PDF")
    ch1 = o_srv.create_chapter(proj.id, "Chapter 1: The Beginning", summary="Beginning chapter.")
    sc_srv.create_scene(ch1.id, "Scene 1", prose="The journey begins on an autumn morning with golden leaves.")

    pdf_bytes = exp_srv.export_pdf(proj.id)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_docx_export(services):
    """Verify python-docx produces valid DOCX bytes."""
    s_srv = services["story"]
    o_srv = services["outline"]
    sc_srv = services["scene"]
    exp_srv = services["export"]

    proj = s_srv.create_project(title="DOCX Test Story", premise="Testing DOCX")
    ch1 = o_srv.create_chapter(proj.id, "Chapter 1", summary="Chapter 1 summary")
    sc_srv.create_scene(ch1.id, "Scene 1", prose="Prose for DOCX document.")

    docx_bytes = exp_srv.export_docx(proj.id)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 500
    assert docx_bytes.startswith(b"PK")  # ZIP-based DOCX magic bytes


def test_backup_and_safe_restore(services):
    """Verify project ZIP creation, preview, and restore with ID conflict handling."""
    s_srv = services["story"]
    o_srv = services["outline"]
    sc_srv = services["scene"]
    b_srv = services["bible"]
    bak_srv = services["backup"]

    # Create original project
    proj = s_srv.create_project(title="Original Backup Project", premise="Backup premise")
    ch = o_srv.create_chapter(proj.id, "Chapter A")
    sc_srv.create_scene(ch.id, "Scene A", prose="Prose A")
    b_srv.create_character(proj.id, "Character A")

    # Create backup ZIP
    zip_bytes = bak_srv.create_project_backup(proj.id)
    assert isinstance(zip_bytes, bytes)
    assert zip_bytes.startswith(b"PK")

    # Preview backup
    preview = bak_srv.preview_backup(zip_bytes)
    assert preview["valid"] is True
    assert preview["title"] == "Original Backup Project"
    assert preview["chapter_count"] == 1
    assert preview["scene_count"] == 1

    # Restore as copy (no overwrite)
    restored_proj = bak_srv.restore_project(preview["data"], overwrite_existing=False)
    assert restored_proj.id != proj.id
    assert "(Restored)" in restored_proj.title

    # Verify restored project has chapters and scenes
    restored_chapters = o_srv.list_chapters(restored_proj.id)
    assert len(restored_chapters) == 1
    restored_scenes = sc_srv.list_scenes_by_chapter(restored_chapters[0].id)
    assert len(restored_scenes) == 1
    assert restored_scenes[0].prose == "Prose A"
