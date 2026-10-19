"""Outline generation and chapter structure management service."""

import logging
from typing import Optional, List, Dict, Any

from storybook.models import Chapter, OutlineResponse, OutlineChapterProposal
from storybook.repositories import (
    ChapterRepository,
    ProjectRepository,
    VersionHistoryRepository,
    AIJobRepository,
)
from storybook.providers.provider_manager import provider_manager, ProviderExecutionResult

logger = logging.getLogger(__name__)


class OutlineService:
    """Service handling story outlines and chapter lifecycle."""

    def __init__(
        self,
        chapter_repo: Optional[ChapterRepository] = None,
        project_repo: Optional[ProjectRepository] = None,
        version_repo: Optional[VersionHistoryRepository] = None,
        job_repo: Optional[AIJobRepository] = None,
    ):
        self.chapter_repo = chapter_repo or ChapterRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.version_repo = version_repo or VersionHistoryRepository()
        self.job_repo = job_repo or AIJobRepository()

    def generate_outline_proposal(
        self, project_id: str, num_chapters: int = 5, preferred_provider: Optional[str] = None
    ) -> ProviderExecutionResult:
        """Generate structured outline proposals from story premise and synopsis."""
        project = self.project_repo.get(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        job = self.job_repo.create_job(
            project_id=project_id,
            job_type="outline_generation",
            input_snapshot={
                "premise": project.premise,
                "synopsis": project.synopsis,
                "num_chapters": num_chapters,
            },
        )

        try:
            job.status = "running"
            job.progress_message = f"Generating {num_chapters}-chapter outline..."
            self.job_repo.update_job(job)

            def _run(provider):
                return provider.generate_outline(
                    premise=project.premise,
                    synopsis=project.synopsis or project.premise,
                    num_chapters=num_chapters,
                )

            exec_result = provider_manager.execute_with_fallback(
                operation_name="generate_outline",
                func=_run,
                preferred_provider=preferred_provider,
            )

            outline: OutlineResponse = exec_result.data

            # Store generated proposal in project metadata for preview/approval
            meta = project.metadata_json or {}
            meta["latest_outline_proposal"] = outline.model_dump()
            project.metadata_json = meta
            self.project_repo.update(project)

            job.status = "completed"
            job.progress_message = "Outline generated successfully."
            job.result_json = outline.model_dump()
            self.job_repo.update_job(job)

            return exec_result
        except Exception as e:
            job.status = "failed"
            job.progress_message = "Outline generation failed."
            job.error_text = str(e)
            self.job_repo.update_job(job)
            raise

    def apply_outline_to_project(
        self, project_id: str, outline: OutlineResponse, overwrite_existing: bool = False
    ) -> List[Chapter]:
        """Convert approved outline proposal chapters into database Chapter records."""
        existing_chapters = self.chapter_repo.list_by_project(project_id)

        if existing_chapters and overwrite_existing:
            # Preserve current state before replacing
            for ch in existing_chapters:
                self.version_repo.record_snapshot(
                    entity_type="chapter",
                    entity_id=ch.id,
                    snapshot=ch.model_dump(),
                    reason="Archived prior to outline replacement",
                )
                self.chapter_repo.delete(ch.id)
            start_index = 1
        else:
            start_index = len(existing_chapters) + 1

        created_chapters = []
        for prop in outline.chapters:
            new_ch = Chapter(
                project_id=project_id,
                order_index=prop.order_index if overwrite_existing else start_index,
                title=prop.title,
                summary=prop.summary,
                status="draft",
            )
            saved = self.chapter_repo.create(new_ch)
            created_chapters.append(saved)
            if not overwrite_existing:
                start_index += 1

        return created_chapters

    def create_chapter(
        self, project_id: str, title: str, summary: str = "", order_index: Optional[int] = None
    ) -> Chapter:
        if order_index is None:
            existing = self.chapter_repo.list_by_project(project_id)
            order_index = len(existing) + 1

        chapter = Chapter(
            project_id=project_id,
            order_index=order_index,
            title=title.strip() or f"Chapter {order_index}",
            summary=summary.strip(),
            status="draft",
        )
        return self.chapter_repo.create(chapter)

    def get_chapter(self, chapter_id: str) -> Optional[Chapter]:
        return self.chapter_repo.get(chapter_id)

    def list_chapters(self, project_id: str) -> List[Chapter]:
        return self.chapter_repo.list_by_project(project_id)

    def update_chapter(self, chapter: Chapter) -> Chapter:
        self.version_repo.record_snapshot(
            entity_type="chapter",
            entity_id=chapter.id,
            snapshot=chapter.model_dump(),
            reason="Chapter updated",
        )
        return self.chapter_repo.update(chapter)

    def delete_chapter(self, chapter_id: str) -> bool:
        chapter = self.chapter_repo.get(chapter_id)
        if chapter:
            self.version_repo.record_snapshot(
                entity_type="chapter",
                entity_id=chapter.id,
                snapshot=chapter.model_dump(),
                reason="Chapter deleted",
            )
        return self.chapter_repo.delete(chapter_id)

    def reorder_chapters(self, project_id: str, chapter_ids: List[str]) -> None:
        self.chapter_repo.reorder(project_id, chapter_ids)
