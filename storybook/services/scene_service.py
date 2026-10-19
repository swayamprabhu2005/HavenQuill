"""Scene breakdown, drafting, revision, and structural management service."""

import logging
from typing import Optional, List, Dict, Any, Tuple

from storybook.models import (
    Scene,
    SceneProposal,
    SceneBreakdownResponse,
    SceneRewriteResponse,
)
from storybook.repositories import (
    SceneRepository,
    ChapterRepository,
    ProjectRepository,
    VersionHistoryRepository,
    AIJobRepository,
)
from storybook.providers.provider_manager import provider_manager, ProviderExecutionResult

logger = logging.getLogger(__name__)


class SceneService:
    """Service managing scene creation, AI breakdown, prose drafting, rewriting, and reordering."""

    def __init__(
        self,
        scene_repo: Optional[SceneRepository] = None,
        chapter_repo: Optional[ChapterRepository] = None,
        project_repo: Optional[ProjectRepository] = None,
        version_repo: Optional[VersionHistoryRepository] = None,
        job_repo: Optional[AIJobRepository] = None,
    ):
        self.scene_repo = scene_repo or SceneRepository()
        self.chapter_repo = chapter_repo or ChapterRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.version_repo = version_repo or VersionHistoryRepository()
        self.job_repo = job_repo or AIJobRepository()

    def generate_scene_breakdown_proposal(
        self, chapter_id: str, num_scenes: int = 3, preferred_provider: Optional[str] = None
    ) -> ProviderExecutionResult:
        """Generate structured scene proposals for a specific chapter."""
        chapter = self.chapter_repo.get(chapter_id)
        if not chapter:
            raise ValueError(f"Chapter '{chapter_id}' not found.")

        job = self.job_repo.create_job(
            project_id=chapter.project_id,
            job_type="scene_breakdown",
            input_snapshot={
                "chapter_id": chapter_id,
                "chapter_title": chapter.title,
                "chapter_summary": chapter.summary,
                "num_scenes": num_scenes,
            },
        )

        try:
            job.status = "running"
            job.progress_message = f"Generating {num_scenes}-scene breakdown for '{chapter.title}'..."
            self.job_repo.update_job(job)

            def _run(provider):
                return provider.generate_scene_breakdown(
                    chapter_title=chapter.title,
                    chapter_summary=chapter.summary or chapter.title,
                    num_scenes=num_scenes,
                )

            exec_result = provider_manager.execute_with_fallback(
                operation_name="generate_scene_breakdown",
                func=_run,
                preferred_provider=preferred_provider,
            )

            breakdown: SceneBreakdownResponse = exec_result.data
            breakdown.chapter_id = chapter_id
            breakdown.chapter_title = chapter.title

            job.status = "completed"
            job.progress_message = "Scene breakdown generated successfully."
            job.result_json = breakdown.model_dump()
            self.job_repo.update_job(job)

            return exec_result
        except Exception as e:
            job.status = "failed"
            job.progress_message = "Scene breakdown failed."
            job.error_text = str(e)
            self.job_repo.update_job(job)
            raise

    def apply_scenes_to_chapter(
        self, chapter_id: str, breakdown: SceneBreakdownResponse, overwrite_existing: bool = False
    ) -> List[Scene]:
        """Convert approved scene proposals into database Scene records."""
        existing_scenes = self.scene_repo.list_by_chapter(chapter_id)

        if existing_scenes and overwrite_existing:
            for sc in existing_scenes:
                self.version_repo.record_snapshot(
                    entity_type="scene",
                    entity_id=sc.id,
                    snapshot=sc.model_dump(),
                    reason="Archived prior to scene breakdown replacement",
                )
                self.scene_repo.delete(sc.id)
            start_index = 1
        else:
            start_index = len(existing_scenes) + 1

        created_scenes = []
        for prop in breakdown.scenes:
            new_sc = Scene(
                chapter_id=chapter_id,
                order_index=prop.order_index if overwrite_existing else start_index,
                title=prop.title,
                summary=prop.summary,
                purpose=prop.purpose,
                pov=prop.pov,
                location_name=prop.location,
                time_marker=prop.time_marker,
                characters_present=prop.characters_present,
                emotional_shift=prop.emotional_shift,
                continuity_json={"dependencies": prop.continuity_dependencies, "dramatic_conflict": prop.dramatic_conflict},
                prose=prop.scene_prose or "",
                status="draft",
                camera_framing=prop.camera_framing or "",
                mood_atmosphere=prop.mood_atmosphere or "",
                visual_summary=prop.visual_summary or "",
            )
            saved = self.scene_repo.create(new_sc)
            created_scenes.append(saved)
            if not overwrite_existing:
                start_index += 1

        return created_scenes

    def create_scene(
        self,
        chapter_id: str,
        title: str,
        summary: str = "",
        prose: str = "",
        pov: str = "",
        location_name: str = "",
        time_marker: str = "",
        characters_present: Optional[List[str]] = None,
        order_index: Optional[int] = None,
    ) -> Scene:
        if order_index is None:
            existing = self.scene_repo.list_by_chapter(chapter_id)
            order_index = len(existing) + 1

        scene = Scene(
            chapter_id=chapter_id,
            order_index=order_index,
            title=title.strip() or f"Scene {order_index}",
            summary=summary.strip(),
            prose=prose.strip(),
            pov=pov.strip(),
            location_name=location_name.strip(),
            time_marker=time_marker.strip(),
            characters_present=characters_present or [],
            status="draft",
        )
        return self.scene_repo.create(scene)

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        return self.scene_repo.get(scene_id)

    def list_scenes_by_chapter(self, chapter_id: str) -> List[Scene]:
        return self.scene_repo.list_by_chapter(chapter_id)

    def list_scenes_by_project(self, project_id: str) -> List[Scene]:
        return self.scene_repo.list_by_project(project_id)

    def update_scene(self, scene: Scene) -> Scene:
        self.version_repo.record_snapshot(
            entity_type="scene",
            entity_id=scene.id,
            snapshot=scene.model_dump(),
            reason="Scene updated",
        )
        return self.scene_repo.update(scene)

    def delete_scene(self, scene_id: str) -> bool:
        scene = self.scene_repo.get(scene_id)
        if scene:
            self.version_repo.record_snapshot(
                entity_type="scene",
                entity_id=scene.id,
                snapshot=scene.model_dump(),
                reason="Scene deleted",
            )
        return self.scene_repo.delete(scene_id)

    def move_scene(self, scene_id: str, direction: str) -> bool:
        """Move scene up or down within its chapter."""
        target_scene = self.scene_repo.get(scene_id)
        if not target_scene:
            return False

        chapter_scenes = self.scene_repo.list_by_chapter(target_scene.chapter_id)
        current_idx = next((i for i, s in enumerate(chapter_scenes) if s.id == scene_id), -1)
        if current_idx == -1:
            return False

        if direction == "up" and current_idx > 0:
            swap_idx = current_idx - 1
        elif direction == "down" and current_idx < len(chapter_scenes) - 1:
            swap_idx = current_idx + 1
        else:
            return False

        # Swap elements in list
        chapter_scenes[current_idx], chapter_scenes[swap_idx] = (
            chapter_scenes[swap_idx],
            chapter_scenes[current_idx],
        )

        ordered_ids = [s.id for s in chapter_scenes]
        self.scene_repo.reorder(target_scene.chapter_id, ordered_ids)
        return True

    def split_scene(self, scene_id: str, split_char_index: int, second_title: str) -> Tuple[Scene, Scene]:
        """Split a scene into two consecutive scenes."""
        orig = self.scene_repo.get(scene_id)
        if not orig:
            raise ValueError(f"Scene '{scene_id}' not found.")

        # Archive original snapshot
        self.version_repo.record_snapshot(
            entity_type="scene",
            entity_id=orig.id,
            snapshot=orig.model_dump(),
            reason="Archived before scene split",
        )

        full_prose = orig.prose or ""
        prose_part1 = full_prose[:split_char_index].strip()
        prose_part2 = full_prose[split_char_index:].strip()

        # Update first scene
        orig.prose = prose_part1
        self.scene_repo.update(orig)

        # Insert second scene right after
        new_scene = Scene(
            chapter_id=orig.chapter_id,
            order_index=orig.order_index + 1,
            title=second_title.strip() or f"{orig.title} (Part 2)",
            summary=f"Continuation of {orig.title}",
            prose=prose_part2,
            pov=orig.pov,
            location_name=orig.location_name,
            time_marker=orig.time_marker,
            characters_present=list(orig.characters_present),
            status="draft",
        )
        saved_second = self.scene_repo.create(new_scene)

        # Re-index subsequent scenes in the chapter
        all_scenes = self.scene_repo.list_by_chapter(orig.chapter_id)
        ordered_ids = [s.id for s in all_scenes if s.id != saved_second.id]
        insert_pos = next((i for i, s in enumerate(all_scenes) if s.id == orig.id), len(ordered_ids) - 1) + 1
        ordered_ids.insert(insert_pos, saved_second.id)
        self.scene_repo.reorder(orig.chapter_id, ordered_ids)

        return orig, saved_second

    def merge_scenes(self, scene_id_1: str, scene_id_2: str) -> Scene:
        """Merge second scene into the first scene."""
        sc1 = self.scene_repo.get(scene_id_1)
        sc2 = self.scene_repo.get(scene_id_2)
        if not sc1 or not sc2:
            raise ValueError("Both scenes must exist to perform merge.")

        self.version_repo.record_snapshot(
            entity_type="scene",
            entity_id=sc1.id,
            snapshot=sc1.model_dump(),
            reason=f"Archived before merging with scene {sc2.id}",
        )
        self.version_repo.record_snapshot(
            entity_type="scene",
            entity_id=sc2.id,
            snapshot=sc2.model_dump(),
            reason="Archived prior to deletion via merge",
        )

        # Combine summaries and prose
        combined_summary = f"{sc1.summary}\n\n{sc2.summary}".strip()
        combined_prose = f"{sc1.prose}\n\n{sc2.prose}".strip()
        combined_chars = list(set(sc1.characters_present + sc2.characters_present))

        sc1.summary = combined_summary
        sc1.prose = combined_prose
        sc1.characters_present = combined_chars
        self.scene_repo.update(sc1)

        # Delete second scene and re-index
        self.scene_repo.delete(sc2.id)
        remaining = self.scene_repo.list_by_chapter(sc1.chapter_id)
        self.scene_repo.reorder(sc1.chapter_id, [s.id for s in remaining])

        return sc1

    def duplicate_scene(self, scene_id: str) -> Scene:
        """Create a duplicate copy of a scene."""
        orig = self.scene_repo.get(scene_id)
        if not orig:
            raise ValueError(f"Scene '{scene_id}' not found.")

        dup = Scene(
            chapter_id=orig.chapter_id,
            order_index=orig.order_index + 1,
            title=f"{orig.title} (Copy)",
            summary=orig.summary,
            prose=orig.prose,
            purpose=orig.purpose,
            pov=orig.pov,
            location_name=orig.location_name,
            time_marker=orig.time_marker,
            emotional_shift=orig.emotional_shift,
            continuity_json=dict(orig.continuity_json),
            status="draft",
            characters_present=list(orig.characters_present),
            camera_framing=orig.camera_framing,
            mood_atmosphere=orig.mood_atmosphere,
            visual_summary=orig.visual_summary,
        )
        saved = self.scene_repo.create(dup)
        all_scenes = self.scene_repo.list_by_chapter(orig.chapter_id)
        ordered_ids = [s.id for s in all_scenes if s.id != saved.id]
        insert_pos = next((i for i, s in enumerate(all_scenes) if s.id == orig.id), len(ordered_ids) - 1) + 1
        ordered_ids.insert(insert_pos, saved.id)
        self.scene_repo.reorder(orig.chapter_id, ordered_ids)
        return saved

    # AI Drafting & Rewriting
    def draft_scene_prose(
        self, scene_id: str, instructions: str = "", preferred_provider: Optional[str] = None
    ) -> ProviderExecutionResult:
        """Draft prose for an approved scene proposal."""
        scene = self.scene_repo.get(scene_id)
        if not scene:
            raise ValueError(f"Scene '{scene_id}' not found.")

        chapter = self.chapter_repo.get(scene.chapter_id)
        context = f"Chapter Title: {chapter.title if chapter else ''}\nChapter Summary: {chapter.summary if chapter else ''}"

        proposal = SceneProposal(
            order_index=scene.order_index,
            title=scene.title,
            summary=scene.summary,
            purpose=scene.purpose,
            pov=scene.pov,
            location=scene.location_name or "",
            time_marker=scene.time_marker,
            characters_present=scene.characters_present,
            dramatic_conflict=scene.continuity_json.get("dramatic_conflict", ""),
            emotional_shift=scene.emotional_shift,
            continuity_dependencies=scene.continuity_json.get("dependencies", []),
            scene_prose=scene.prose,
        )

        def _run(provider):
            return provider.draft_scene_prose(scene=proposal, context=context, instructions=instructions)

        exec_result = provider_manager.execute_with_fallback(
            operation_name="draft_scene_prose",
            func=_run,
            preferred_provider=preferred_provider,
        )

        generated_prose: str = exec_result.data

        # Record snapshot of existing prose before replacing
        if scene.prose:
            self.version_repo.record_snapshot(
                entity_type="scene",
                entity_id=scene.id,
                snapshot=scene.model_dump(),
                reason="Archived prior to AI prose generation",
            )

        scene.prose = generated_prose
        scene.status = "revised"
        self.scene_repo.update(scene)

        return exec_result

    def rewrite_scene_prose(
        self, scene_id: str, instructions: str, tone: str = "", preferred_provider: Optional[str] = None
    ) -> ProviderExecutionResult:
        """Rewrite or refine existing prose for a scene."""
        scene = self.scene_repo.get(scene_id)
        if not scene:
            raise ValueError(f"Scene '{scene_id}' not found.")
        if not scene.prose:
            raise ValueError("Scene has no prose to rewrite. Use Draft Prose first.")

        def _run(provider):
            return provider.rewrite_scene(scene_prose=scene.prose, instructions=instructions, tone=tone)

        exec_result = provider_manager.execute_with_fallback(
            operation_name="rewrite_scene_prose",
            func=_run,
            preferred_provider=preferred_provider,
        )

        rewrite_resp: SceneRewriteResponse = exec_result.data

        # Archive existing prose before replacing
        self.version_repo.record_snapshot(
            entity_type="scene",
            entity_id=scene.id,
            snapshot=scene.model_dump(),
            reason=f"Archived before AI rewrite: {instructions[:40]}",
        )

        scene.prose = rewrite_resp.rewritten_prose
        scene.status = "revised"
        self.scene_repo.update(scene)

        return exec_result
