"""Domain and Pydantic models for Storybook Studio."""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import uuid


def generate_uuid() -> str:
    """Generate a clean UUID string."""
    return str(uuid.uuid4())


# ============================================================
# Core Database Entities
# ============================================================

class Project(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    title: str
    subtitle: Optional[str] = ""
    genre: str = "General Fiction"
    tone: str = "Engaging"
    language: str = "English"
    intended_audience: Optional[str] = ""
    premise: str = ""
    synopsis: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class SourceDraft(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    project_id: str
    source_type: str = "typed"  # typed, audio, imported_txt, imported_pdf, imported_docx
    original_text: str = ""
    transcript_text: str = ""
    source_filename: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Chapter(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    project_id: str
    order_index: int = 1
    title: str = "Untitled Chapter"
    summary: str = ""
    prose: str = ""
    status: str = "draft"  # draft, in_progress, completed
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Scene(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    chapter_id: str
    order_index: int = 1
    title: str = "Untitled Scene"
    summary: str = ""
    prose: str = ""
    purpose: str = ""
    pov: str = ""
    location_id: Optional[str] = ""
    time_marker: str = ""
    emotional_shift: str = ""
    continuity_json: Dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"  # draft, revised, completed
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Future image / comic panel generation compatibility fields (Phase 1: optional / structured)
    characters_present: List[str] = Field(default_factory=list)
    location_name: Optional[str] = ""
    camera_framing: Optional[str] = ""  # e.g., "Medium two-shot, eye-level"
    mood_atmosphere: Optional[str] = ""  # e.g., "Tense, dimly lit, rain outside"
    visual_summary: Optional[str] = ""   # Future visual prompt for image generation
    dialogue_snippet: Optional[str] = ""


class Character(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    project_id: str
    canonical_name: str
    aliases_json: List[str] = Field(default_factory=list)
    description: str = ""
    traits_json: List[str] = Field(default_factory=list)
    relationships_json: Dict[str, str] = Field(default_factory=dict)
    locked_fields_json: List[str] = Field(default_factory=list)  # fields marked as canonical/locked


class Location(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    project_id: str
    name: str
    description: str = ""
    rules_json: List[str] = Field(default_factory=list)


class CanonFact(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    project_id: str
    category: str = "world"  # world, character, plot, timeline, rule
    subject: str = ""
    fact_text: str
    is_locked: bool = False
    source_scene_id: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StoryEvent(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    project_id: str
    order_index: int = 1
    time_marker: str = ""
    description: str
    related_scene_ids_json: List[str] = Field(default_factory=list)


class AIJob(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    project_id: str
    job_type: str
    input_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    status: str = "queued"  # queued, running, completed, failed, cancelled
    progress_message: str = ""
    result_json: Optional[Dict[str, Any]] = None
    error_text: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class VersionHistory(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    entity_type: str  # project, chapter, scene, story_bible
    entity_id: str
    content_snapshot_json: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    reason: str = "Manual edit or AI generation"


# ============================================================
# Structured Output AI Schemas
# ============================================================

class StoryDevelopmentResponse(BaseModel):
    logline: str = Field(..., description="One-sentence compelling hook summarizing protagonist, conflict, and stakes.")
    short_synopsis: str = Field(..., description="Concise synopsis of the core narrative arc.")
    detailed_synopsis: str = Field(..., description="Comprehensive synopsis broken into narrative movements.")
    themes: List[str] = Field(default_factory=list, description="Central thematic motifs.")
    main_conflict: str = Field(..., description="Primary dramatic tension or obstacle.")
    main_character_goals: List[str] = Field(default_factory=list, description="Desires and objectives driving protagonists.")
    major_turning_points: List[str] = Field(default_factory=list, description="Critical moments that redirect the plot.")
    proposed_ending: str = Field(..., description="Proposed climax and resolution.")
    open_questions: List[str] = Field(default_factory=list, description="Unresolved creative questions needing user decisions.")
    assumptions: List[str] = Field(default_factory=list, description="Explicit assumptions made to flesh out the story.")


class OutlineChapterProposal(BaseModel):
    order_index: int
    title: str
    summary: str
    character_arcs: List[str] = Field(default_factory=list)
    turning_points: List[str] = Field(default_factory=list)
    important_revelations: List[str] = Field(default_factory=list)
    setup_and_payoff: List[str] = Field(default_factory=list)
    proposed_resolution: str = ""


class OutlineResponse(BaseModel):
    chapters: List[OutlineChapterProposal] = Field(default_factory=list)
    overall_arc: Optional[str] = ""


class SceneProposal(BaseModel):
    order_index: int
    title: str
    summary: str
    purpose: str = ""
    pov: str = ""
    location: str = ""
    time_marker: str = ""
    characters_present: List[str] = Field(default_factory=list)
    dramatic_conflict: str = ""
    emotional_shift: str = ""
    continuity_dependencies: List[str] = Field(default_factory=list)
    scene_prose: Optional[str] = ""

    # Future image & visual panel generation metadata
    camera_framing: Optional[str] = ""
    mood_atmosphere: Optional[str] = ""
    visual_summary: Optional[str] = ""


class SceneBreakdownResponse(BaseModel):
    chapter_id: Optional[str] = None
    chapter_title: Optional[str] = None
    scenes: List[SceneProposal] = Field(default_factory=list)


class CharacterExtraction(BaseModel):
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)
    description: str = ""
    traits: List[str] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(default_factory=dict)


class LocationExtraction(BaseModel):
    name: str
    description: str = ""
    rules: List[str] = Field(default_factory=list)


class CanonFactExtraction(BaseModel):
    category: str = "world"  # world, character, plot, rule
    subject: str = ""
    fact_text: str
    is_locked: bool = False


class StoryBibleExtractionResponse(BaseModel):
    characters: List[CharacterExtraction] = Field(default_factory=list)
    locations: List[LocationExtraction] = Field(default_factory=list)
    canon_facts: List[CanonFactExtraction] = Field(default_factory=list)


class ContinuityIssue(BaseModel):
    category: str  # fact_conflict, timeline_conflict, character_knowledge, name_inconsistency, missing_setup, repetition, motivation_shift
    severity: str = "medium"  # high, medium, low
    description: str
    related_entities: List[str] = Field(default_factory=list)
    suggested_fix: str = ""


class ContinuityReviewResponse(BaseModel):
    summary: str
    consistency_score: int = Field(default=85, ge=1, le=100)
    issues: List[ContinuityIssue] = Field(default_factory=list)


class SceneRewriteResponse(BaseModel):
    rewritten_prose: str
    summary_of_changes: str
