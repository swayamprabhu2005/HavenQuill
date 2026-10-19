"""Automated unit tests for ScriptService and ScriptRepository in HavenQuill."""

import pytest
from pathlib import Path
from storybook.database import DatabaseManager
from storybook.models import Project, Chapter, Scene, Script
from storybook.repositories import (
    ProjectRepository,
    ChapterRepository,
    SceneRepository,
    ScriptRepository,
    VersionHistoryRepository,
)
from storybook.services.script_service import ScriptService


@pytest.fixture
def script_service(test_db: DatabaseManager) -> ScriptService:
    return ScriptService(
        script_repo=ScriptRepository(test_db),
        chapter_repo=ChapterRepository(test_db),
        project_repo=ProjectRepository(test_db),
        scene_repo=SceneRepository(test_db),
        version_repo=VersionHistoryRepository(test_db),
    )


@pytest.fixture
def sample_project(test_db: DatabaseManager) -> Project:
    proj_repo = ProjectRepository(test_db)
    return proj_repo.create(
        Project(
            title="The Clockwork Arch",
            genre="Steampunk",
            tone="Atmospheric",
            premise="An archivist decodes a clockwork chronometer.",
        )
    )


def test_script_repository_crud(test_db: DatabaseManager, sample_project: Project):
    repo = ScriptRepository(test_db)

    # 1. Create script
    script = repo.create(
        Script(
            project_id=sample_project.id,
            title="The Clockwork Arch - Screenplay",
            script_content="INT. ARCHIVE - NIGHT\nElena examines the clock.",
            covered_chapters_json=["chap-1"],
            last_chapter_index=1,
        )
    )
    assert script.id is not None
    assert script.project_id == sample_project.id

    # 2. Get by project
    fetched = repo.get_by_project(sample_project.id)
    assert fetched is not None
    assert fetched.id == script.id
    assert "INT. ARCHIVE" in fetched.script_content
    assert fetched.covered_chapters_json == ["chap-1"]

    # 3. Update script
    fetched.script_content = "INT. ARCHIVE - NIGHT\nElena opens the secret compartment."
    fetched.covered_chapters_json = ["chap-1", "chap-2"]
    updated = repo.update(fetched)
    assert "secret compartment" in updated.script_content
    assert len(updated.covered_chapters_json) == 2

    # 4. Delete
    deleted = repo.delete(script.id)
    assert deleted is True
    assert repo.get_by_project(sample_project.id) is None


def test_chapter_coverage_calculation(
    test_db: DatabaseManager, script_service: ScriptService, sample_project: Project
):
    chap_repo = ChapterRepository(test_db)
    ch1 = chap_repo.create(Chapter(project_id=sample_project.id, title="The Discovery", order_index=1, prose="Elena found the device."))
    ch2 = chap_repo.create(Chapter(project_id=sample_project.id, title="The Pursuit", order_index=2, prose="The guards arrived."))

    # Initially, no chapters covered
    status1 = script_service.get_chapter_coverage_status(sample_project.id)
    assert status1["total_chapters"] == 2
    assert len(status1["covered_chapters"]) == 0
    assert len(status1["pending_chapters"]) == 2
    assert status1["is_up_to_date"] is False

    # Simulate adapting Chapter 1
    script = script_service.get_or_create_script(sample_project.id)
    script.script_content = "INT. GRAND ARCHIVE - NIGHT\nElena holds the device."
    script.covered_chapters_json = [ch1.id]
    script_service.script_repo.update(script)

    status2 = script_service.get_chapter_coverage_status(sample_project.id)
    assert len(status2["covered_chapters"]) == 1
    assert len(status2["pending_chapters"]) == 1
    assert status2["pending_chapters"][0].id == ch2.id
    assert status2["is_up_to_date"] is False


def test_adapt_book_to_script_initial_and_continuation(
    test_db: DatabaseManager, script_service: ScriptService, sample_project: Project
):
    chap_repo = ChapterRepository(test_db)
    ch1 = chap_repo.create(Chapter(project_id=sample_project.id, title="Part I", order_index=1, prose="Elena started her journey."))

    # 1. Initial adaptation with Mock Provider
    script, res = script_service.adapt_book_to_script(
        project_id=sample_project.id,
        regenerate_all=True,
        preferred_provider="mock",
    )
    assert script.id is not None
    assert res.provider_name == "mock"
    assert "INT." in script.script_content
    assert ch1.id in script.covered_chapters_json

    # 2. Add second chapter (the next half of the book)
    ch2 = chap_repo.create(Chapter(project_id=sample_project.id, title="Part II", order_index=2, prose="Elena reached the spire."))

    # Check that chapter 2 is pending
    coverage = script_service.get_chapter_coverage_status(sample_project.id)
    assert len(coverage["pending_chapters"]) == 1
    assert coverage["pending_chapters"][0].id == ch2.id

    # 3. Incremental continuation (sends existing script + new chapter)
    continued_script, cont_res = script_service.adapt_book_to_script(
        project_id=sample_project.id,
        regenerate_all=False,
        preferred_provider="mock",
    )
    assert cont_res.provider_name == "mock"
    assert ch1.id in continued_script.covered_chapters_json
    assert ch2.id in continued_script.covered_chapters_json

    # Coverage is now 100% up to date
    new_coverage = script_service.get_chapter_coverage_status(sample_project.id)
    assert new_coverage["is_up_to_date"] is True


def test_script_export_pdf_and_fountain(
    test_db: DatabaseManager, script_service: ScriptService, sample_project: Project, tmp_path: Path
):
    script = Script(
        project_id=sample_project.id,
        title="The Clockwork Arch - Screenplay",
        script_content=(
            "FADE IN:\n\n"
            "INT. GRAND ARCHIVE - NIGHT\n\n"
            "Elena examines the brass chronometer.\n\n"
            "ELENA\n"
            "(whispering)\n"
            "The gears are turning backward.\n\n"
            "FADE OUT."
        ),
    )

    # Test PDF export
    pdf_path = tmp_path / "screenplay_test.pdf"
    exported_path = script_service.export_script_pdf(script, pdf_path)
    assert exported_path.exists()
    assert exported_path.stat().st_size > 500

    # Test Fountain export
    fountain_text = script_service.export_script_fountain(script)
    assert "Title: The Clockwork Arch - Screenplay" in fountain_text
    assert "ELENA" in fountain_text
    assert "INT. GRAND ARCHIVE" in fountain_text
