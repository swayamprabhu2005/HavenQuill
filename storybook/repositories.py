"""Data access repositories for Storybook Studio entities."""

import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from storybook.database import DatabaseManager, db_manager
from storybook.models import (
    Project, SourceDraft, Chapter, Scene, Character, Location,
    CanonFact, StoryEvent, AIJob, VersionHistory
)

logger = logging.getLogger(__name__)


class ProjectRepository:
    """Repository for managing projects."""

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db

    def create(self, project: Project) -> Project:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, title, subtitle, genre, tone, language,
                    intended_audience, premise, synopsis, created_at,
                    updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.id, project.title, project.subtitle or "", project.genre,
                    project.tone, project.language, project.intended_audience or "",
                    project.premise or "", project.synopsis or "", project.created_at,
                    project.updated_at, json.dumps(project.metadata_json)
                )
            )
            conn.commit()
        return project

    def get(self, project_id: str) -> Optional[Project]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Project(
                id=row["id"],
                title=row["title"],
                subtitle=row["subtitle"],
                genre=row["genre"],
                tone=row["tone"],
                language=row["language"],
                intended_audience=row["intended_audience"],
                premise=row["premise"],
                synopsis=row["synopsis"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata_json=json.loads(row["metadata_json"] or "{}")
            )

    def list_all(self) -> List[Project]:
        projects = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            for row in cur.fetchall():
                projects.append(Project(
                    id=row["id"],
                    title=row["title"],
                    subtitle=row["subtitle"],
                    genre=row["genre"],
                    tone=row["tone"],
                    language=row["language"],
                    intended_audience=row["intended_audience"],
                    premise=row["premise"],
                    synopsis=row["synopsis"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata_json=json.loads(row["metadata_json"] or "{}")
                ))
        return projects

    def update(self, project: Project) -> Project:
        project.updated_at = datetime.utcnow().isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE projects SET
                    title = ?, subtitle = ?, genre = ?, tone = ?, language = ?,
                    intended_audience = ?, premise = ?, synopsis = ?,
                    updated_at = ?, metadata_json = ?
                WHERE id = ?
                """,
                (
                    project.title, project.subtitle or "", project.genre,
                    project.tone, project.language, project.intended_audience or "",
                    project.premise or "", project.synopsis or "", project.updated_at,
                    json.dumps(project.metadata_json), project.id
                )
            )
            conn.commit()
        return project

    def delete(self, project_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cur.rowcount > 0

    def get_stats(self, project_id: str) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM chapters WHERE project_id = ?", (project_id,))
            chapter_count = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(*) FROM scenes s
                JOIN chapters c ON s.chapter_id = c.id
                WHERE c.project_id = ?
                """,
                (project_id,)
            )
            scene_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM characters WHERE project_id = ?", (project_id,))
            character_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM source_drafts WHERE project_id = ?", (project_id,))
            draft_count = cur.fetchone()[0]

            return {
                "chapter_count": chapter_count,
                "scene_count": scene_count,
                "character_count": character_count,
                "draft_count": draft_count,
            }


class SourceDraftRepository:
    """Repository for managing original text, voice transcripts, and imported drafts."""

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db

    def create(self, draft: SourceDraft) -> SourceDraft:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO source_drafts (
                    id, project_id, source_type, original_text,
                    transcript_text, source_filename, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    draft.id, draft.project_id, draft.source_type,
                    draft.original_text, draft.transcript_text or "",
                    draft.source_filename or "", draft.created_at
                )
            )
            conn.commit()
        return draft

    def list_by_project(self, project_id: str) -> List[SourceDraft]:
        drafts = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM source_drafts WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
            for row in cur.fetchall():
                drafts.append(SourceDraft(
                    id=row["id"],
                    project_id=row["project_id"],
                    source_type=row["source_type"],
                    original_text=row["original_text"],
                    transcript_text=row["transcript_text"],
                    source_filename=row["source_filename"],
                    created_at=row["created_at"]
                ))
        return drafts

    def get(self, draft_id: str) -> Optional[SourceDraft]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM source_drafts WHERE id = ?", (draft_id,))
            row = cur.fetchone()
            if not row:
                return None
            return SourceDraft(
                id=row["id"],
                project_id=row["project_id"],
                source_type=row["source_type"],
                original_text=row["original_text"],
                transcript_text=row["transcript_text"],
                source_filename=row["source_filename"],
                created_at=row["created_at"]
            )

    def delete(self, draft_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM source_drafts WHERE id = ?", (draft_id,))
            conn.commit()
            return cur.rowcount > 0


class ChapterRepository:
    """Repository for managing chapters."""

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db

    def create(self, chapter: Chapter) -> Chapter:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chapters (
                    id, project_id, order_index, title,
                    summary, prose, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chapter.id, chapter.project_id, chapter.order_index, chapter.title,
                    chapter.summary or "", chapter.prose or "", chapter.status,
                    chapter.created_at, chapter.updated_at
                )
            )
            conn.commit()
        return chapter

    def get(self, chapter_id: str) -> Optional[Chapter]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM chapters WHERE id = ?", (chapter_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Chapter(
                id=row["id"],
                project_id=row["project_id"],
                order_index=row["order_index"],
                title=row["title"],
                summary=row["summary"],
                prose=row["prose"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    def list_by_project(self, project_id: str) -> List[Chapter]:
        chapters = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM chapters WHERE project_id = ? ORDER BY order_index ASC", (project_id,))
            for row in cur.fetchall():
                chapters.append(Chapter(
                    id=row["id"],
                    project_id=row["project_id"],
                    order_index=row["order_index"],
                    title=row["title"],
                    summary=row["summary"],
                    prose=row["prose"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                ))
        return chapters

    def update(self, chapter: Chapter) -> Chapter:
        chapter.updated_at = datetime.utcnow().isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE chapters SET
                    order_index = ?, title = ?, summary = ?,
                    prose = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    chapter.order_index, chapter.title, chapter.summary or "",
                    chapter.prose or "", chapter.status, chapter.updated_at,
                    chapter.id
                )
            )
            conn.commit()
        return chapter

    def delete(self, chapter_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
            conn.commit()
            return cur.rowcount > 0

    def reorder(self, project_id: str, chapter_ids_ordered: List[str]) -> None:
        with self.db.get_connection() as conn:
            for idx, ch_id in enumerate(chapter_ids_ordered, start=1):
                conn.execute(
                    "UPDATE chapters SET order_index = ?, updated_at = ? WHERE id = ? AND project_id = ?",
                    (idx, datetime.utcnow().isoformat(), ch_id, project_id)
                )
            conn.commit()


class SceneRepository:
    """Repository for managing scenes with full future image generation compatibility."""

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db

    def _row_to_scene(self, row: sqlite3.Row) -> Scene:
        return Scene(
            id=row["id"],
            chapter_id=row["chapter_id"],
            order_index=row["order_index"],
            title=row["title"],
            summary=row["summary"],
            prose=row["prose"],
            purpose=row["purpose"],
            pov=row["pov"],
            location_id=row["location_id"],
            time_marker=row["time_marker"],
            emotional_shift=row["emotional_shift"],
            continuity_json=json.loads(row["continuity_json"] or "{}"),
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            characters_present=json.loads(row["characters_present"] or "[]"),
            location_name=row["location_name"],
            camera_framing=row["camera_framing"],
            mood_atmosphere=row["mood_atmosphere"],
            visual_summary=row["visual_summary"],
            dialogue_snippet=row["dialogue_snippet"]
        )

    def create(self, scene: Scene) -> Scene:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO scenes (
                    id, chapter_id, order_index, title, summary, prose,
                    purpose, pov, location_id, time_marker, emotional_shift,
                    continuity_json, status, created_at, updated_at,
                    characters_present, location_name, camera_framing,
                    mood_atmosphere, visual_summary, dialogue_snippet
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scene.id, scene.chapter_id, scene.order_index, scene.title,
                    scene.summary or "", scene.prose or "", scene.purpose or "",
                    scene.pov or "", scene.location_id or "", scene.time_marker or "",
                    scene.emotional_shift or "", json.dumps(scene.continuity_json),
                    scene.status, scene.created_at, scene.updated_at,
                    json.dumps(scene.characters_present), scene.location_name or "",
                    scene.camera_framing or "", scene.mood_atmosphere or "",
                    scene.visual_summary or "", scene.dialogue_snippet or ""
                )
            )
            conn.commit()
        return scene

    def get(self, scene_id: str) -> Optional[Scene]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_scene(row)

    def list_by_chapter(self, chapter_id: str) -> List[Scene]:
        scenes = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM scenes WHERE chapter_id = ? ORDER BY order_index ASC", (chapter_id,))
            for row in cur.fetchall():
                scenes.append(self._row_to_scene(row))
        return scenes

    def list_by_project(self, project_id: str) -> List[Scene]:
        scenes = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.* FROM scenes s
                JOIN chapters c ON s.chapter_id = c.id
                WHERE c.project_id = ?
                ORDER BY c.order_index ASC, s.order_index ASC
                """,
                (project_id,)
            )
            for row in cur.fetchall():
                scenes.append(self._row_to_scene(row))
        return scenes

    def update(self, scene: Scene) -> Scene:
        scene.updated_at = datetime.utcnow().isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE scenes SET
                    chapter_id = ?, order_index = ?, title = ?, summary = ?,
                    prose = ?, purpose = ?, pov = ?, location_id = ?,
                    time_marker = ?, emotional_shift = ?, continuity_json = ?,
                    status = ?, updated_at = ?, characters_present = ?,
                    location_name = ?, camera_framing = ?, mood_atmosphere = ?,
                    visual_summary = ?, dialogue_snippet = ?
                WHERE id = ?
                """,
                (
                    scene.chapter_id, scene.order_index, scene.title,
                    scene.summary or "", scene.prose or "", scene.purpose or "",
                    scene.pov or "", scene.location_id or "", scene.time_marker or "",
                    scene.emotional_shift or "", json.dumps(scene.continuity_json),
                    scene.status, scene.updated_at, json.dumps(scene.characters_present),
                    scene.location_name or "", scene.camera_framing or "",
                    scene.mood_atmosphere or "", scene.visual_summary or "",
                    scene.dialogue_snippet or "", scene.id
                )
            )
            conn.commit()
        return scene

    def delete(self, scene_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM scenes WHERE id = ?", (scene_id,))
            conn.commit()
            return cur.rowcount > 0

    def reorder(self, chapter_id: str, scene_ids_ordered: List[str]) -> None:
        with self.db.get_connection() as conn:
            for idx, sc_id in enumerate(scene_ids_ordered, start=1):
                conn.execute(
                    "UPDATE scenes SET order_index = ?, updated_at = ? WHERE id = ? AND chapter_id = ?",
                    (idx, datetime.utcnow().isoformat(), sc_id, chapter_id)
                )
            conn.commit()


class StoryBibleRepository:
    """Repository for Characters, Locations, Canon Facts, and Story Events."""

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db

    # Characters
    def create_character(self, char: Character) -> Character:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO characters (
                    id, project_id, canonical_name, aliases_json,
                    description, traits_json, relationships_json, locked_fields_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    char.id, char.project_id, char.canonical_name,
                    json.dumps(char.aliases_json), char.description or "",
                    json.dumps(char.traits_json), json.dumps(char.relationships_json),
                    json.dumps(char.locked_fields_json)
                )
            )
            conn.commit()
        return char

    def list_characters(self, project_id: str) -> List[Character]:
        chars = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM characters WHERE project_id = ? ORDER BY canonical_name ASC", (project_id,))
            for row in cur.fetchall():
                chars.append(Character(
                    id=row["id"],
                    project_id=row["project_id"],
                    canonical_name=row["canonical_name"],
                    aliases_json=json.loads(row["aliases_json"] or "[]"),
                    description=row["description"],
                    traits_json=json.loads(row["traits_json"] or "[]"),
                    relationships_json=json.loads(row["relationships_json"] or "{}"),
                    locked_fields_json=json.loads(row["locked_fields_json"] or "[]")
                ))
        return chars

    def update_character(self, char: Character) -> Character:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE characters SET
                    canonical_name = ?, aliases_json = ?, description = ?,
                    traits_json = ?, relationships_json = ?, locked_fields_json = ?
                WHERE id = ?
                """,
                (
                    char.canonical_name, json.dumps(char.aliases_json),
                    char.description or "", json.dumps(char.traits_json),
                    json.dumps(char.relationships_json), json.dumps(char.locked_fields_json),
                    char.id
                )
            )
            conn.commit()
        return char

    def delete_character(self, character_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM characters WHERE id = ?", (character_id,))
            conn.commit()
            return cur.rowcount > 0

    # Locations
    def create_location(self, loc: Location) -> Location:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO locations (id, project_id, name, description, rules_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (loc.id, loc.project_id, loc.name, loc.description or "", json.dumps(loc.rules_json))
            )
            conn.commit()
        return loc

    def list_locations(self, project_id: str) -> List[Location]:
        locs = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM locations WHERE project_id = ? ORDER BY name ASC", (project_id,))
            for row in cur.fetchall():
                locs.append(Location(
                    id=row["id"],
                    project_id=row["project_id"],
                    name=row["name"],
                    description=row["description"],
                    rules_json=json.loads(row["rules_json"] or "[]")
                ))
        return locs

    def update_location(self, loc: Location) -> Location:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE locations SET name = ?, description = ?, rules_json = ?
                WHERE id = ?
                """,
                (loc.name, loc.description or "", json.dumps(loc.rules_json), loc.id)
            )
            conn.commit()
        return loc

    def delete_location(self, location_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM locations WHERE id = ?", (location_id,))
            conn.commit()
            return cur.rowcount > 0

    # Canon Facts
    def create_canon_fact(self, fact: CanonFact) -> CanonFact:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO canon_facts (
                    id, project_id, category, subject,
                    fact_text, is_locked, source_scene_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fact.id, fact.project_id, fact.category, fact.subject or "",
                    fact.fact_text, 1 if fact.is_locked else 0,
                    fact.source_scene_id or "", fact.created_at
                )
            )
            conn.commit()
        return fact

    def list_canon_facts(self, project_id: str) -> List[CanonFact]:
        facts = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM canon_facts WHERE project_id = ? ORDER BY created_at ASC", (project_id,))
            for row in cur.fetchall():
                facts.append(CanonFact(
                    id=row["id"],
                    project_id=row["project_id"],
                    category=row["category"],
                    subject=row["subject"],
                    fact_text=row["fact_text"],
                    is_locked=bool(row["is_locked"]),
                    source_scene_id=row["source_scene_id"],
                    created_at=row["created_at"]
                ))
        return facts

    def update_canon_fact(self, fact: CanonFact) -> CanonFact:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE canon_facts SET
                    category = ?, subject = ?, fact_text = ?, is_locked = ?
                WHERE id = ?
                """,
                (fact.category, fact.subject or "", fact.fact_text, 1 if fact.is_locked else 0, fact.id)
            )
            conn.commit()
        return fact

    def delete_canon_fact(self, fact_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM canon_facts WHERE id = ?", (fact_id,))
            conn.commit()
            return cur.rowcount > 0

    # Story Events
    def create_story_event(self, event: StoryEvent) -> StoryEvent:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO story_events (
                    id, project_id, order_index, time_marker,
                    description, related_scene_ids_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id, event.project_id, event.order_index,
                    event.time_marker or "", event.description,
                    json.dumps(event.related_scene_ids_json)
                )
            )
            conn.commit()
        return event

    def list_story_events(self, project_id: str) -> List[StoryEvent]:
        events = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM story_events WHERE project_id = ? ORDER BY order_index ASC", (project_id,))
            for row in cur.fetchall():
                events.append(StoryEvent(
                    id=row["id"],
                    project_id=row["project_id"],
                    order_index=row["order_index"],
                    time_marker=row["time_marker"],
                    description=row["description"],
                    related_scene_ids_json=json.loads(row["related_scene_ids_json"] or "[]")
                ))
        return events

    def delete_story_event(self, event_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM story_events WHERE id = ?", (event_id,))
            conn.commit()
            return cur.rowcount > 0


class VersionHistoryRepository:
    """Repository for version control and snapshots of story edits."""

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db

    def record_snapshot(self, entity_type: str, entity_id: str, snapshot: Dict[str, Any], reason: str = "") -> VersionHistory:
        vh = VersionHistory(
            entity_type=entity_type,
            entity_id=entity_id,
            content_snapshot_json=snapshot,
            reason=reason or "Snapshot recorded"
        )
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO version_history (id, entity_type, entity_id, content_snapshot_json, created_at, reason)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (vh.id, vh.entity_type, vh.entity_id, json.dumps(vh.content_snapshot_json), vh.created_at, vh.reason)
            )
            conn.commit()
        return vh

    def get_history(self, entity_type: str, entity_id: str, limit: int = 20) -> List[VersionHistory]:
        history = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM version_history
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (entity_type, entity_id, limit)
            )
            for row in cur.fetchall():
                history.append(VersionHistory(
                    id=row["id"],
                    entity_type=row["entity_type"],
                    entity_id=row["entity_id"],
                    content_snapshot_json=json.loads(row["content_snapshot_json"]),
                    created_at=row["created_at"],
                    reason=row["reason"]
                ))
        return history


class AIJobRepository:
    """Repository for tracking AI tasks, progress, snapshots, and results."""

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db

    def create_job(self, project_id: str, job_type: str, input_snapshot: Dict[str, Any]) -> AIJob:
        job = AIJob(
            project_id=project_id,
            job_type=job_type,
            input_snapshot_json=input_snapshot,
            status="queued",
            progress_message="Job queued"
        )
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ai_jobs (
                    id, project_id, job_type, input_snapshot_json,
                    status, progress_message, result_json, error_text,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id, job.project_id, job.job_type,
                    json.dumps(job.input_snapshot_json), job.status,
                    job.progress_message, None, None,
                    job.created_at, job.updated_at
                )
            )
            conn.commit()
        return job

    def update_job(self, job: AIJob) -> AIJob:
        job.updated_at = datetime.utcnow().isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE ai_jobs SET
                    status = ?, progress_message = ?, result_json = ?,
                    error_text = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    job.status, job.progress_message,
                    json.dumps(job.result_json) if job.result_json is not None else None,
                    job.error_text, job.updated_at, job.id
                )
            )
            conn.commit()
        return job

    def get_job(self, job_id: str) -> Optional[AIJob]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM ai_jobs WHERE id = ?", (job_id,))
            row = cur.fetchone()
            if not row:
                return None
            return AIJob(
                id=row["id"],
                project_id=row["project_id"],
                job_type=row["job_type"],
                input_snapshot_json=json.loads(row["input_snapshot_json"] or "{}"),
                status=row["status"],
                progress_message=row["progress_message"],
                result_json=json.loads(row["result_json"]) if row["result_json"] else None,
                error_text=row["error_text"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    def list_jobs(self, project_id: str, limit: int = 10) -> List[AIJob]:
        jobs = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM ai_jobs WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
                (project_id, limit)
            )
            for row in cur.fetchall():
                jobs.append(AIJob(
                    id=row["id"],
                    project_id=row["project_id"],
                    job_type=row["job_type"],
                    input_snapshot_json=json.loads(row["input_snapshot_json"] or "{}"),
                    status=row["status"],
                    progress_message=row["progress_message"],
                    result_json=json.loads(row["result_json"]) if row["result_json"] else None,
                    error_text=row["error_text"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                ))
        return jobs
