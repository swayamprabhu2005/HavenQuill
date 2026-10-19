"""Story development and project management service."""

import logging
from typing import Optional, List, Dict, Any

from storybook.models import Project, SourceDraft, StoryDevelopmentResponse
from storybook.repositories import (
    ProjectRepository,
    SourceDraftRepository,
    VersionHistoryRepository,
    AIJobRepository,
)
from storybook.providers.provider_manager import provider_manager, ProviderExecutionResult

logger = logging.getLogger(__name__)


class StoryService:
    """Service managing project lifecycles, source drafts, and high-level story development."""

    def __init__(
        self,
        project_repo: Optional[ProjectRepository] = None,
        draft_repo: Optional[SourceDraftRepository] = None,
        version_repo: Optional[VersionHistoryRepository] = None,
        job_repo: Optional[AIJobRepository] = None,
    ):
        self.project_repo = project_repo or ProjectRepository()
        self.draft_repo = draft_repo or SourceDraftRepository()
        self.version_repo = version_repo or VersionHistoryRepository()
        self.job_repo = job_repo or AIJobRepository()

    def create_project(
        self,
        title: str,
        subtitle: str = "",
        genre: str = "General Fiction",
        tone: str = "Engaging",
        language: str = "English",
        intended_audience: str = "",
        premise: str = "",
        synopsis: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Project:
        """Create a new story project."""
        project = Project(
            title=title.strip() or "Untitled Story",
            subtitle=subtitle.strip(),
            genre=genre.strip() or "General Fiction",
            tone=tone.strip() or "Engaging",
            language=language.strip() or "English",
            intended_audience=intended_audience.strip(),
            premise=premise.strip(),
            synopsis=synopsis.strip(),
            metadata_json=metadata or {},
        )
        saved = self.project_repo.create(project)
        self.version_repo.record_snapshot(
            entity_type="project",
            entity_id=saved.id,
            snapshot=saved.model_dump(),
            reason="Project created",
        )
        return saved

    def get_project(self, project_id: str) -> Optional[Project]:
        return self.project_repo.get(project_id)

    def list_projects(self) -> List[Project]:
        return self.project_repo.list_all()

    def update_project(self, project: Project) -> Project:
        self.version_repo.record_snapshot(
            entity_type="project",
            entity_id=project.id,
            snapshot=project.model_dump(),
            reason="Project details updated",
        )
        return self.project_repo.update(project)

    def delete_project(self, project_id: str) -> bool:
        return self.project_repo.delete(project_id)

    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        return self.project_repo.get_stats(project_id)

    # Source Draft Management
    def save_source_draft(
        self,
        project_id: str,
        source_type: str,
        original_text: str,
        transcript_text: str = "",
        source_filename: str = "",
    ) -> SourceDraft:
        """Preserve raw author input (typed, audio transcript, or imported file)."""
        draft = SourceDraft(
            project_id=project_id,
            source_type=source_type,
            original_text=original_text,
            transcript_text=transcript_text,
            source_filename=source_filename,
        )
        return self.draft_repo.create(draft)

    def list_source_drafts(self, project_id: str) -> List[SourceDraft]:
        return self.draft_repo.list_by_project(project_id)

    def get_source_draft(self, draft_id: str) -> Optional[SourceDraft]:
        return self.draft_repo.get(draft_id)

    def delete_source_draft(self, draft_id: str) -> bool:
        return self.draft_repo.delete(draft_id)

    # Story Development Workflow
    def develop_story(
        self, project_id: str, notes: str = "", preferred_provider: Optional[str] = None
    ) -> ProviderExecutionResult:
        """Generate comprehensive story development packet using AI."""
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # Create an AI job tracking record
        job = self.job_repo.create_job(
            project_id=project_id,
            job_type="story_development",
            input_snapshot={
                "premise": project.premise,
                "genre": project.genre,
                "tone": project.tone,
                "audience": project.intended_audience,
                "notes": notes,
            },
        )

        try:
            job.status = "running"
            job.progress_message = "Analyzing premise and building story foundation..."
            self.job_repo.update_job(job)

            def _run(provider):
                return provider.generate_story_development(
                    premise=project.premise,
                    genre=project.genre,
                    tone=project.tone,
                    audience=project.intended_audience or "",
                    notes=notes,
                )

            exec_result = provider_manager.execute_with_fallback(
                operation_name="develop_story",
                func=_run,
                preferred_provider=preferred_provider,
            )

            story_dev: StoryDevelopmentResponse = exec_result.data

            # Update project metadata with story development results
            meta = project.metadata_json or {}
            meta["story_development"] = story_dev.model_dump()
            meta["last_provider"] = exec_result.provider_name
            meta["last_model"] = exec_result.model_name
            project.metadata_json = meta

            if not project.synopsis or project.synopsis == project.premise:
                project.synopsis = story_dev.short_synopsis

            self.update_project(project)

            job.status = "completed"
            job.progress_message = f"Story developed successfully with {exec_result.provider_name}."
            job.result_json = story_dev.model_dump()
            self.job_repo.update_job(job)

            return exec_result

        except Exception as e:
            job.status = "failed"
            job.progress_message = "Story development failed."
            job.error_text = str(e)
            self.job_repo.update_job(job)
            raise
