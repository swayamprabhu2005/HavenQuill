"""Story Bible service managing characters, locations, canon facts, and canonical locking."""

import logging
from typing import Optional, List, Dict, Any

from storybook.models import (
    Character,
    Location,
    CanonFact,
    StoryEvent,
    StoryBibleExtractionResponse,
)
from storybook.repositories import (
    StoryBibleRepository,
    ProjectRepository,
    VersionHistoryRepository,
    AIJobRepository,
)
from storybook.providers.provider_manager import provider_manager, ProviderExecutionResult

logger = logging.getLogger(__name__)


class StoryBibleService:
    """Service managing characters, locations, locked canon facts, and world building."""

    def __init__(
        self,
        bible_repo: Optional[StoryBibleRepository] = None,
        project_repo: Optional[ProjectRepository] = None,
        version_repo: Optional[VersionHistoryRepository] = None,
        job_repo: Optional[AIJobRepository] = None,
    ):
        self.bible_repo = bible_repo or StoryBibleRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.version_repo = version_repo or VersionHistoryRepository()
        self.job_repo = job_repo or AIJobRepository()

    # Characters
    def create_character(
        self,
        project_id: str,
        name: str,
        description: str = "",
        aliases: Optional[List[str]] = None,
        traits: Optional[List[str]] = None,
        relationships: Optional[Dict[str, str]] = None,
        locked_fields: Optional[List[str]] = None,
    ) -> Character:
        char = Character(
            project_id=project_id,
            canonical_name=name.strip(),
            description=description.strip(),
            aliases_json=aliases or [],
            traits_json=traits or [],
            relationships_json=relationships or {},
            locked_fields_json=locked_fields or [],
        )
        saved = self.bible_repo.create_character(char)
        self.version_repo.record_snapshot(
            entity_type="character",
            entity_id=saved.id,
            snapshot=saved.model_dump(),
            reason="Character created",
        )
        return saved

    def list_characters(self, project_id: str) -> List[Character]:
        return self.bible_repo.list_characters(project_id)

    def update_character(self, character: Character) -> Character:
        self.version_repo.record_snapshot(
            entity_type="character",
            entity_id=character.id,
            snapshot=character.model_dump(),
            reason="Character updated",
        )
        return self.bible_repo.update_character(character)

    def delete_character(self, character_id: str) -> bool:
        return self.bible_repo.delete_character(character_id)

    # Locations
    def create_location(
        self, project_id: str, name: str, description: str = "", rules: Optional[List[str]] = None
    ) -> Location:
        loc = Location(
            project_id=project_id,
            name=name.strip(),
            description=description.strip(),
            rules_json=rules or [],
        )
        return self.bible_repo.create_location(loc)

    def list_locations(self, project_id: str) -> List[Location]:
        return self.bible_repo.list_locations(project_id)

    def update_location(self, loc: Location) -> Location:
        return self.bible_repo.update_location(loc)

    def delete_location(self, location_id: str) -> bool:
        return self.bible_repo.delete_location(location_id)

    # Canon Facts & Canonical Locking
    def create_canon_fact(
        self,
        project_id: str,
        fact_text: str,
        category: str = "world",
        subject: str = "",
        is_locked: bool = False,
        source_scene_id: str = "",
    ) -> CanonFact:
        fact = CanonFact(
            project_id=project_id,
            category=category,
            subject=subject.strip(),
            fact_text=fact_text.strip(),
            is_locked=is_locked,
            source_scene_id=source_scene_id,
        )
        saved = self.bible_repo.create_canon_fact(fact)
        self.version_repo.record_snapshot(
            entity_type="canon_fact",
            entity_id=saved.id,
            snapshot=saved.model_dump(),
            reason=f"Canon fact created (locked={is_locked})",
        )
        return saved

    def list_canon_facts(self, project_id: str) -> List[CanonFact]:
        return self.bible_repo.list_canon_facts(project_id)

    def update_canon_fact(self, fact: CanonFact) -> CanonFact:
        return self.bible_repo.update_canon_fact(fact)

    def toggle_fact_lock(self, fact_id: str, is_locked: bool) -> Optional[CanonFact]:
        facts = self.bible_repo.list_canon_facts(project_id="")
        # Direct lookup
        target = next((f for f in facts if f.id == fact_id), None)
        if target:
            target.is_locked = is_locked
            return self.bible_repo.update_canon_fact(target)
        return None

    def delete_canon_fact(self, fact_id: str) -> bool:
        return self.bible_repo.delete_canon_fact(fact_id)

    # Story Events
    def create_story_event(
        self, project_id: str, description: str, time_marker: str = "", order_index: int = 1
    ) -> StoryEvent:
        event = StoryEvent(
            project_id=project_id,
            description=description.strip(),
            time_marker=time_marker.strip(),
            order_index=order_index,
        )
        return self.bible_repo.create_story_event(event)

    def list_story_events(self, project_id: str) -> List[StoryEvent]:
        return self.bible_repo.list_story_events(project_id)

    def delete_story_event(self, event_id: str) -> bool:
        return self.bible_repo.delete_story_event(event_id)

    # AI Extraction and Canon Safeguards
    def extract_story_bible_from_text(
        self, project_id: str, text: str, preferred_provider: Optional[str] = None
    ) -> ProviderExecutionResult:
        """Extract characters, locations, and canon facts from source text."""
        def _run(provider):
            return provider.extract_story_bible(text=text)

        exec_result = provider_manager.execute_with_fallback(
            operation_name="extract_story_bible",
            func=_run,
            preferred_provider=preferred_provider,
        )

        extraction: StoryBibleExtractionResponse = exec_result.data

        # Store in project metadata as pending extraction for user review
        project = self.project_repo.get(project_id)
        if project:
            meta = project.metadata_json or {}
            meta["latest_story_bible_extraction"] = extraction.model_dump()
            project.metadata_json = meta
            self.project_repo.update(project)

        return exec_result

    def apply_extracted_story_bible(
        self, project_id: str, extraction: StoryBibleExtractionResponse
    ) -> Dict[str, int]:
        """Apply approved extracted entities to the database."""
        added_counts = {"characters": 0, "locations": 0, "facts": 0}

        # Characters
        existing_chars = {c.canonical_name.lower(): c for c in self.list_characters(project_id)}
        for ch in extraction.characters:
            if ch.canonical_name.lower() not in existing_chars:
                self.create_character(
                    project_id=project_id,
                    name=ch.canonical_name,
                    description=ch.description,
                    aliases=ch.aliases,
                    traits=ch.traits,
                    relationships=ch.relationships,
                )
                added_counts["characters"] += 1

        # Locations
        existing_locs = {l.name.lower(): l for l in self.list_locations(project_id)}
        for loc in extraction.locations:
            if loc.name.lower() not in existing_locs:
                self.create_location(
                    project_id=project_id,
                    name=loc.name,
                    description=loc.description,
                    rules=loc.rules,
                )
                added_counts["locations"] += 1

        # Facts
        for fact in extraction.canon_facts:
            self.create_canon_fact(
                project_id=project_id,
                fact_text=fact.fact_text,
                category=fact.category,
                subject=fact.subject,
                is_locked=fact.is_locked,
            )
            added_counts["facts"] += 1

        return added_counts

    def check_for_canon_contradictions(
        self, project_id: str, candidate_text: str
    ) -> List[str]:
        """
        Check if candidate text contradicts any locked canonical facts.
        Returns a list of warning messages if potential conflicts are detected.
        """
        locked_facts = [f for f in self.list_canon_facts(project_id) if f.is_locked]
        warnings = []
        lower_cand = candidate_text.lower()

        for fact in locked_facts:
            subj = fact.subject.lower()
            if subj and subj in lower_cand:
                # Flag potential conflict check
                warnings.append(
                    f"Warning: Locked Canon Fact regarding '{fact.subject}': \"{fact.fact_text}\". "
                    "Please verify your edit does not contradict this canon."
                )

        return warnings
