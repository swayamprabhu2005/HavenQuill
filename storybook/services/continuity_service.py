"""Continuity checking and narrative consistency review service."""

import logging
from typing import Optional, List, Dict, Any

from storybook.models import ContinuityReviewResponse
from storybook.repositories import (
    StoryBibleRepository,
    SceneRepository,
    ProjectRepository,
    AIJobRepository,
)
from storybook.providers.provider_manager import provider_manager, ProviderExecutionResult

logger = logging.getLogger(__name__)


class ContinuityService:
    """Service auditing story consistency against canon facts and scene progression."""

    def __init__(
        self,
        bible_repo: Optional[StoryBibleRepository] = None,
        scene_repo: Optional[SceneRepository] = None,
        project_repo: Optional[ProjectRepository] = None,
        job_repo: Optional[AIJobRepository] = None,
    ):
        self.bible_repo = bible_repo or StoryBibleRepository()
        self.scene_repo = scene_repo or SceneRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.job_repo = job_repo or AIJobRepository()

    def audit_project_continuity(
        self, project_id: str, preferred_provider: Optional[str] = None
    ) -> ProviderExecutionResult:
        """Run an AI continuity review of the project."""
        project = self.project_repo.get(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # Gather canon facts
        canon_facts = self.bible_repo.list_canon_facts(project_id)
        fact_strings = [
            f"[{f.category.upper()}] {f.subject}: {f.fact_text} {'(LOCKED)' if f.is_locked else ''}"
            for f in canon_facts
        ]

        # Gather scene summaries
        scenes = self.scene_repo.list_by_project(project_id)
        scene_strings = [
            f"Scene #{s.order_index} '{s.title}' (Location: {s.location_name}, Time: {s.time_marker}, POV: {s.pov}): {s.summary}"
            for s in scenes
        ]

        if not fact_strings and not scene_strings:
            raise ValueError(
                "Cannot perform continuity review without established canon facts or scenes. "
                "Please add scenes or story bible facts first."
            )

        job = self.job_repo.create_job(
            project_id=project_id,
            job_type="continuity_review",
            input_snapshot={
                "num_facts": len(fact_strings),
                "num_scenes": len(scene_strings),
            },
        )

        try:
            job.status = "running"
            job.progress_message = "Reviewing story continuity and timeline dependencies..."
            self.job_repo.update_job(job)

            def _run(provider):
                return provider.review_continuity(
                    story_bible_facts=fact_strings,
                    scene_summaries=scene_strings,
                )

            exec_result = provider_manager.execute_with_fallback(
                operation_name="review_continuity",
                func=_run,
                preferred_provider=preferred_provider,
            )

            review: ContinuityReviewResponse = exec_result.data

            # Store in project metadata for persistent display
            meta = project.metadata_json or {}
            meta["latest_continuity_review"] = review.model_dump()
            project.metadata_json = meta
            self.project_repo.update(project)

            job.status = "completed"
            job.progress_message = f"Continuity review completed (Score: {review.consistency_score}/100)."
            job.result_json = review.model_dump()
            self.job_repo.update_job(job)

            return exec_result
        except Exception as e:
            job.status = "failed"
            job.progress_message = "Continuity review failed."
            job.error_text = str(e)
            self.job_repo.update_job(job)
            raise
