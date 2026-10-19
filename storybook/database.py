"""SQLite database connection and schema management for Storybook Studio."""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from storybook.config import config

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Schema migration version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT DEFAULT '',
    genre TEXT DEFAULT 'General Fiction',
    tone TEXT DEFAULT 'Engaging',
    language TEXT DEFAULT 'English',
    intended_audience TEXT DEFAULT '',
    premise TEXT DEFAULT '',
    synopsis TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

-- Source drafts (typed text, audio transcripts, imported files)
CREATE TABLE IF NOT EXISTS source_drafts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    original_text TEXT NOT NULL,
    transcript_text TEXT DEFAULT '',
    source_filename TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Chapters table
CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT DEFAULT '',
    prose TEXT DEFAULT '',
    status TEXT DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Scenes table (includes future image/comic generation metadata)
CREATE TABLE IF NOT EXISTS scenes (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT DEFAULT '',
    prose TEXT DEFAULT '',
    purpose TEXT DEFAULT '',
    pov TEXT DEFAULT '',
    location_id TEXT DEFAULT '',
    time_marker TEXT DEFAULT '',
    emotional_shift TEXT DEFAULT '',
    continuity_json TEXT DEFAULT '{}',
    status TEXT DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    characters_present TEXT DEFAULT '[]',
    location_name TEXT DEFAULT '',
    camera_framing TEXT DEFAULT '',
    mood_atmosphere TEXT DEFAULT '',
    visual_summary TEXT DEFAULT '',
    dialogue_snippet TEXT DEFAULT '',
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

-- Characters table
CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases_json TEXT DEFAULT '[]',
    description TEXT DEFAULT '',
    traits_json TEXT DEFAULT '[]',
    relationships_json TEXT DEFAULT '{}',
    locked_fields_json TEXT DEFAULT '[]',
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Locations table
CREATE TABLE IF NOT EXISTS locations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    rules_json TEXT DEFAULT '[]',
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Canon facts table
CREATE TABLE IF NOT EXISTS canon_facts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    category TEXT DEFAULT 'world',
    subject TEXT DEFAULT '',
    fact_text TEXT NOT NULL,
    is_locked INTEGER DEFAULT 0,
    source_scene_id TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Story events table
CREATE TABLE IF NOT EXISTS story_events (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    time_marker TEXT DEFAULT '',
    description TEXT NOT NULL,
    related_scene_ids_json TEXT DEFAULT '[]',
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- AI Jobs table
CREATE TABLE IF NOT EXISTS ai_jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    input_snapshot_json TEXT DEFAULT '{}',
    status TEXT DEFAULT 'queued',
    progress_message TEXT DEFAULT '',
    result_json TEXT DEFAULT NULL,
    error_text TEXT DEFAULT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Version History table
CREATE TABLE IF NOT EXISTS version_history (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    content_snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    reason TEXT DEFAULT 'Manual edit or AI generation'
);

-- Live Story Scribe Segments (Streaming Flow & RAG Memory)
CREATE TABLE IF NOT EXISTS story_segments (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    segment_index INTEGER NOT NULL,
    raw_input TEXT NOT NULL,
    generated_prose TEXT DEFAULT '',
    status TEXT DEFAULT 'pending', -- pending, processed
    word_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Performance and isolation indexes
CREATE INDEX IF NOT EXISTS idx_drafts_project ON source_drafts(project_id);
CREATE INDEX IF NOT EXISTS idx_chapters_project ON chapters(project_id, order_index);
CREATE INDEX IF NOT EXISTS idx_scenes_chapter ON scenes(chapter_id, order_index);
CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_id);
CREATE INDEX IF NOT EXISTS idx_locations_project ON locations(project_id);
CREATE INDEX IF NOT EXISTS idx_segments_project ON story_segments(project_id, segment_index);
CREATE INDEX IF NOT EXISTS idx_canon_project ON canon_facts(project_id);
CREATE INDEX IF NOT EXISTS idx_events_project ON story_events(project_id, order_index);
CREATE INDEX IF NOT EXISTS idx_version_entity ON version_history(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_jobs_project ON ai_jobs(project_id);
"""


class DatabaseManager:
    """Manages SQLite connections and schema initialization."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with foreign keys and row factory."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_database(self) -> None:
        """Initializes tables, indexes, and schema versions."""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            cur = conn.cursor()
            cur.execute("SELECT version FROM schema_version WHERE version = ?", (SCHEMA_VERSION,))
            row = cur.fetchone()
            if not row:
                cur.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            conn.commit()


# Default singleton instance
db_manager = DatabaseManager()
