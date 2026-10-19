"""Pytest fixtures and configuration for HavenQuill test suite."""

import pytest
import tempfile
from pathlib import Path

from storybook.database import DatabaseManager
from storybook.repositories import (
    ProjectRepository,
    SourceDraftRepository,
    ChapterRepository,
    SceneRepository,
    StoryBibleRepository,
    VersionHistoryRepository,
    AIJobRepository,
)
from storybook.services.story_service import StoryService
from storybook.services.outline_service import OutlineService
from storybook.services.scene_service import SceneService
from storybook.services.character_service import StoryBibleService
from storybook.services.continuity_service import ContinuityService
from storybook.services.export_service import ExportService
from storybook.services.backup_service import BackupService


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a unique temporary SQLite database file for isolation."""
    return tmp_path / "test_storybook.db"


@pytest.fixture
def test_db(temp_db_path):
    """Initialize a fresh isolated DatabaseManager."""
    return DatabaseManager(db_path=temp_db_path)


@pytest.fixture
def repos(test_db):
    """Return an instantiated bundle of all repositories backed by the test DB."""
    return {
        "project": ProjectRepository(db=test_db),
        "draft": SourceDraftRepository(db=test_db),
        "chapter": ChapterRepository(db=test_db),
        "scene": SceneRepository(db=test_db),
        "bible": StoryBibleRepository(db=test_db),
        "version": VersionHistoryRepository(db=test_db),
        "job": AIJobRepository(db=test_db),
    }


@pytest.fixture
def services(repos):
    """Return instantiated service layer backed by test repositories."""
    story_srv = StoryService(
        project_repo=repos["project"],
        draft_repo=repos["draft"],
        version_repo=repos["version"],
        job_repo=repos["job"],
    )
    outline_srv = OutlineService(
        chapter_repo=repos["chapter"],
        project_repo=repos["project"],
        version_repo=repos["version"],
        job_repo=repos["job"],
    )
    scene_srv = SceneService(
        scene_repo=repos["scene"],
        chapter_repo=repos["chapter"],
        project_repo=repos["project"],
        version_repo=repos["version"],
        job_repo=repos["job"],
    )
    bible_srv = StoryBibleService(
        bible_repo=repos["bible"],
        project_repo=repos["project"],
        version_repo=repos["version"],
        job_repo=repos["job"],
    )
    continuity_srv = ContinuityService(
        bible_repo=repos["bible"],
        scene_repo=repos["scene"],
        project_repo=repos["project"],
        job_repo=repos["job"],
    )
    export_srv = ExportService(
        project_repo=repos["project"],
        chapter_repo=repos["chapter"],
        scene_repo=repos["scene"],
        bible_repo=repos["bible"],
    )
    backup_srv = BackupService(
        project_repo=repos["project"],
        chapter_repo=repos["chapter"],
        scene_repo=repos["scene"],
        bible_repo=repos["bible"],
        draft_repo=repos["draft"],
    )

    return {
        "story": story_srv,
        "outline": outline_srv,
        "scene": scene_srv,
        "bible": bible_srv,
        "continuity": continuity_srv,
        "export": export_srv,
        "backup": backup_srv,
    }
