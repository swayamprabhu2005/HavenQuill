"""Backup and restore service for project archives (ZIP packages)."""

import io
import json
import zipfile
import logging
from typing import Dict, Any, Optional, Tuple

from storybook.config import config
from storybook.models import Project, Chapter, Scene, Character, Location, CanonFact, StoryEvent, generate_uuid
from storybook.repositories import (
    ProjectRepository,
    ChapterRepository,
    SceneRepository,
    StoryBibleRepository,
    SourceDraftRepository,
)
from storybook.services.export_service import ExportService, export_service

logger = logging.getLogger(__name__)


class BackupService:
    """Creates and restores self-contained project backup ZIP archives without exposing secrets."""

    def __init__(
        self,
        project_repo: Optional[ProjectRepository] = None,
        chapter_repo: Optional[ChapterRepository] = None,
        scene_repo: Optional[SceneRepository] = None,
        bible_repo: Optional[StoryBibleRepository] = None,
        draft_repo: Optional[SourceDraftRepository] = None,
    ):
        self.project_repo = project_repo or ProjectRepository()
        self.chapter_repo = chapter_repo or ChapterRepository()
        self.scene_repo = scene_repo or SceneRepository()
        self.bible_repo = bible_repo or StoryBibleRepository()
        self.draft_repo = draft_repo or SourceDraftRepository()
        self.export_service = ExportService(
            project_repo=self.project_repo,
            chapter_repo=self.chapter_repo,
            scene_repo=self.scene_repo,
            bible_repo=self.bible_repo,
        )

    def create_project_backup(self, project_id: str) -> bytes:
        """Create a complete ZIP archive for a project."""
        project = self.project_repo.get(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # Full project JSON payload
        project_data = self.export_service.export_json(project_id)

        # Include source drafts
        drafts = self.draft_repo.list_by_project(project_id)
        project_data["source_drafts"] = [d.model_dump() for d in drafts]

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Store main story payload
            zf.writestr("project.json", json.dumps(project_data, indent=2))
            # Store markdown representation for convenience
            md_text = self.export_service.export_markdown(project_id)
            zf.writestr("manuscript.md", md_text)

        return buffer.getvalue()

    def preview_backup(self, zip_bytes: bytes) -> Dict[str, Any]:
        """Inspect and validate a backup archive before committing restore."""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
                if "project.json" not in zf.namelist():
                    raise ValueError("Archive is missing required 'project.json' file.")

                raw_json = zf.read("project.json").decode("utf-8")
                data = json.loads(raw_json)

                # Security check: ensure no keys leaked
                serialized = json.dumps(data).lower()
                for secret in ("gemini_api_key", "groq_api_key", "aiza", "gsk_"):
                    if secret in serialized:
                        raise ValueError("Security violation: backup archive contains credentials or API keys.")

                proj = data.get("project", {})
                chapters = data.get("chapters", [])
                bible = data.get("story_bible", {})

                return {
                    "valid": True,
                    "title": proj.get("title", "Unknown Title"),
                    "genre": proj.get("genre", "General Fiction"),
                    "chapter_count": len(chapters),
                    "scene_count": sum(len(c.get("scenes", [])) for c in chapters),
                    "character_count": len(bible.get("characters", [])),
                    "data": data,
                }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def restore_project(
        self, backup_data: Dict[str, Any], overwrite_existing: bool = False
    ) -> Project:
        """Safely restore a project from validated backup data with ID conflict resolution."""
        proj_info = backup_data.get("project", {})
        original_id = proj_info.get("id")

        existing = self.project_repo.get(original_id) if original_id else None
        if existing and not overwrite_existing:
            # Create a clone with a fresh ID to avoid overwriting
            project_id = generate_uuid()
            title = f"{proj_info.get('title', 'Restored Project')} (Restored)"
        else:
            project_id = original_id or generate_uuid()
            title = proj_info.get("title", "Restored Project")
            if existing and overwrite_existing:
                self.project_repo.delete(project_id)

        # 1. Restore Project
        new_project = Project(
            id=project_id,
            title=title,
            subtitle=proj_info.get("subtitle", ""),
            genre=proj_info.get("genre", "General Fiction"),
            tone=proj_info.get("tone", "Engaging"),
            language=proj_info.get("language", "English"),
            intended_audience=proj_info.get("intended_audience", ""),
            premise=proj_info.get("premise", ""),
            synopsis=proj_info.get("synopsis", ""),
        )
        self.project_repo.create(new_project)

        # 2. Restore Story Bible
        bible = backup_data.get("story_bible", {})
        for ch_data in bible.get("characters", []):
            self.bible_repo.create_character(
                Character(
                    id=generate_uuid(),
                    project_id=project_id,
                    canonical_name=ch_data.get("canonical_name", ""),
                    aliases_json=ch_data.get("aliases_json", []),
                    description=ch_data.get("description", ""),
                    traits_json=ch_data.get("traits_json", []),
                    relationships_json=ch_data.get("relationships_json", {}),
                    locked_fields_json=ch_data.get("locked_fields_json", []),
                )
            )

        for loc_data in bible.get("locations", []):
            self.bible_repo.create_location(
                Location(
                    id=generate_uuid(),
                    project_id=project_id,
                    name=loc_data.get("name", ""),
                    description=loc_data.get("description", ""),
                    rules_json=loc_data.get("rules_json", []),
                )
            )

        for fact_data in bible.get("canon_facts", []):
            self.bible_repo.create_canon_fact(
                CanonFact(
                    id=generate_uuid(),
                    project_id=project_id,
                    category=fact_data.get("category", "world"),
                    subject=fact_data.get("subject", ""),
                    fact_text=fact_data.get("fact_text", ""),
                    is_locked=bool(fact_data.get("is_locked", False)),
                )
            )

        # 3. Restore Chapters and Scenes
        for ch_data in backup_data.get("chapters", []):
            chapter_id = generate_uuid()
            new_ch = Chapter(
                id=chapter_id,
                project_id=project_id,
                order_index=ch_data.get("order_index", 1),
                title=ch_data.get("title", "Untitled Chapter"),
                summary=ch_data.get("summary", ""),
                prose=ch_data.get("prose", ""),
                status=ch_data.get("status", "draft"),
            )
            self.chapter_repo.create(new_ch)

            for sc_data in ch_data.get("scenes", []):
                new_sc = Scene(
                    id=generate_uuid(),
                    chapter_id=chapter_id,
                    order_index=sc_data.get("order_index", 1),
                    title=sc_data.get("title", "Untitled Scene"),
                    summary=sc_data.get("summary", ""),
                    prose=sc_data.get("prose", ""),
                    purpose=sc_data.get("purpose", ""),
                    pov=sc_data.get("pov", ""),
                    location_name=sc_data.get("location_name", ""),
                    time_marker=sc_data.get("time_marker", ""),
                    characters_present=sc_data.get("characters_present", []),
                    emotional_shift=sc_data.get("emotional_shift", ""),
                    continuity_json=sc_data.get("continuity", {}),
                    status=sc_data.get("status", "draft"),
                    camera_framing=sc_data.get("visual_metadata", {}).get("camera_framing", ""),
                    mood_atmosphere=sc_data.get("visual_metadata", {}).get("mood_atmosphere", ""),
                    visual_summary=sc_data.get("visual_metadata", {}).get("visual_summary", ""),
                )
                self.scene_repo.create(new_sc)

        return new_project


backup_service = BackupService()
