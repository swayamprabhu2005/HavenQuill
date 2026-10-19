"""Agentic RAG Rolling Memory Service for Token/Credit Optimization and Streaming Story Flow."""

import logging
from typing import Optional, List, Dict, Any, Tuple

from storybook.models import StorySegment, Project
from storybook.repositories import (
    StorySegmentRepository,
    ProjectRepository,
    ChapterRepository,
    SceneRepository,
    StoryBibleRepository,
    VersionHistoryRepository,
)
from storybook.providers.provider_manager import provider_manager, ProviderExecutionResult

logger = logging.getLogger(__name__)


class AgenticRAGService:
    """
    Manages continuous segment-by-segment story processing with Agentic RAG rolling memory.
    Prevents sending thousands of words of past transcript history to Gemini,
    saving API credits, avoiding rate limits, and ensuring narrative continuity.
    """

    def __init__(
        self,
        segment_repo: Optional[StorySegmentRepository] = None,
        project_repo: Optional[ProjectRepository] = None,
        chapter_repo: Optional[ChapterRepository] = None,
        scene_repo: Optional[SceneRepository] = None,
        bible_repo: Optional[StoryBibleRepository] = None,
        version_repo: Optional[VersionHistoryRepository] = None,
    ):
        self.segment_repo = segment_repo or StorySegmentRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.chapter_repo = chapter_repo or ChapterRepository()
        self.scene_repo = scene_repo or SceneRepository()
        self.bible_repo = bible_repo or StoryBibleRepository()
        self.version_repo = version_repo or VersionHistoryRepository()

    def get_or_create_active_segment(self, project_id: str) -> StorySegment:
        """Fetch the currently active/pending segment for a project or create a new one."""
        segments = self.segment_repo.list_by_project(project_id)
        pending = [s for s in segments if s.status == "pending"]
        if pending:
            return pending[-1]

        # Create fresh next segment
        next_idx = len(segments) + 1
        new_seg = StorySegment(
            project_id=project_id,
            segment_index=next_idx,
            raw_input="",
            status="pending",
            word_count=0,
        )
        return self.segment_repo.create(new_seg)

    def append_text_to_active_segment(
        self, project_id: str, new_text: str
    ) -> StorySegment:
        """Append spoken transcript or typed text to the active pending segment."""
        segment = self.get_or_create_active_segment(project_id)
        if segment.raw_input:
            segment.raw_input = f"{segment.raw_input.strip()} {new_text.strip()}".strip()
        else:
            segment.raw_input = new_text.strip()

        segment.word_count = len(segment.raw_input.split())
        return self.segment_repo.update(segment)

    def check_keyword_boundary(self, text: str) -> Tuple[bool, str]:
        """
        Detects verbal boundary keywords like 'para end', 'paragraph end', 'next part', 'chapter end'.
        Returns (has_keyword, cleaned_text).
        """
        keywords = [
            "para one end", "para end", "paragraph end", "paragraph one end",
            "section end", "next part", "end of para", "end paragraph"
        ]
        lower = text.lower()
        for kw in keywords:
            if kw in lower:
                # Remove the keyword cleanly
                cleaned = lower.replace(kw, "").strip()
                return True, cleaned
        return False, text

    def build_agentic_rag_context(
        self, project_id: str, active_segment: StorySegment
    ) -> Dict[str, Any]:
        """
        Constructs a compact, high-relevance Agentic Context Packet.
        Instead of re-sending thousands of words from previous parts,
        compresses history into a rolling memory recap + seam bridge + canon anchors.
        """
        project = self.project_repo.get(project_id)
        all_segments = self.segment_repo.list_by_project(project_id)

        # Committed segments before this one
        committed = [s for s in all_segments if s.status == "processed" and s.id != active_segment.id]

        # 1. Canon Facts Anchor (strictly locked facts)
        locked_facts = [
            f.fact_text for f in self.bible_repo.list_canon_facts(project_id) if f.is_locked
        ]

        # 2. Key Characters
        chars = [
            f"{c.canonical_name}: {', '.join(c.traits_json[:3])}"
            for c in self.bible_repo.list_characters(project_id)[:5]
        ]

        # 3. Last Narrative Bridge (last 2 sentences of immediately preceding committed prose)
        bridge_sentence = ""
        if committed and committed[-1].generated_prose:
            last_prose = committed[-1].generated_prose.strip()
            sentences = [s.strip() for s in last_prose.split(".") if s.strip()]
            if len(sentences) >= 2:
                bridge_sentence = f"{sentences[-2]}. {sentences[-1]}."
            elif sentences:
                bridge_sentence = f"{sentences[-1]}."

        # 4. Rolling Story Recap (distilled from previous committed parts)
        recap_points = []
        for s in committed[-3:]:  # Focus on last 3 committed segments for immediate momentum
            if s.generated_prose:
                snippet = s.generated_prose[:120].strip() + "..."
                recap_points.append(f"Part {s.segment_index}: {snippet}")

        # Compute token / credit savings estimate
        raw_prior_words = sum(len(s.raw_input.split()) for s in committed)
        context_words = len(" ".join(recap_points + locked_facts + chars).split())
        saved_words = max(0, raw_prior_words - context_words)

        return {
            "project_title": project.title if project else "Story",
            "genre": project.genre if project else "Fiction",
            "tone": project.tone if project else "Atmospheric",
            "premise": project.premise if project else "",
            "locked_facts": locked_facts,
            "characters": chars,
            "bridge_sentence": bridge_sentence,
            "rolling_recap": recap_points,
            "estimated_words_saved": saved_words,
            "segment_index": active_segment.segment_index,
        }

    def process_segment_with_ai(
        self,
        project_id: str,
        segment_id: str,
        custom_instructions: str = "",
        preferred_provider: Optional[str] = None,
    ) -> ProviderExecutionResult:
        """
        Sends ONLY the active segment + distilled Agentic RAG rolling memory to Gemini/Groq.
        Transforms the raw spoken transcript / typed thoughts into rich story prose.
        Tags the segment as processed and creates a commitment boundary.
        """
        segment = self.segment_repo.get(segment_id)
        if not segment:
            raise ValueError(f"Segment '{segment_id}' not found.")

        if not segment.raw_input.strip():
            raise ValueError("Segment is empty. Please speak or type your thoughts first.")

        # Build credit-saving context packet
        rag_context = self.build_agentic_rag_context(project_id, segment)

        system_instruction = (
            "You are an inspiring literary co-author and prose architect. "
            "Your task is to take the author's rough spoken thoughts, voice dictation notes, or raw drafted ideas "
            "for the CURRENT segment, and transform them into immersive, beautifully-crafted narrative prose.\n\n"
            f"STORY FOUNDATION:\n"
            f"Title: {rag_context['project_title']}\n"
            f"Genre: {rag_context['genre']} | Tone: {rag_context['tone']}\n"
            f"Premise: {rag_context['premise']}\n\n"
            "CANON CONSTRAINTS (Do NOT contradict):\n"
            + "\n".join(f"- {f}" for f in rag_context["locked_facts"] or ["None specified"]) + "\n\n"
            "ACTIVE CHARACTERS:\n"
            + "\n".join(f"- {c}" for c in rag_context["characters"] or ["None specified"]) + "\n\n"
            "NARRATIVE BRIDGE (The immediate preceding sentences from prior committed part):\n"
            f"\"{rag_context['bridge_sentence'] or 'Beginning of scene'}\"\n\n"
            "INSTRUCTIONS:\n"
            "- Seamlessly continue the flow from the bridge sentence.\n"
            "- Enrich the author's raw input with sensory detail, atmospheric texture, dialogue, and emotional nuance.\n"
            "- Honor the author's exact plot points and intentions.\n"
            "- Return ONLY the crafted prose for this specific segment without meta-commentary."
        )

        prompt = (
            f"AUTHOR'S RAW INPUT FOR PART {segment.segment_index}:\n"
            f"\"\"\"\n{segment.raw_input.strip()}\n\"\"\"\n\n"
        )
        if custom_instructions:
            prompt += f"SPECIAL AUTHOR NOTES: {custom_instructions.strip()}\n\n"
        prompt += f"Draft the polished narrative prose for Part {segment.segment_index} now."

        def _run(provider):
            return provider.generate_text(prompt, system_instruction=system_instruction)

        exec_result = provider_manager.execute_with_fallback(
            operation_name="process_story_segment",
            func=_run,
            preferred_provider=preferred_provider,
        )

        generated_prose: str = exec_result.data

        # Record snapshot of raw input
        self.version_repo.record_snapshot(
            entity_type="story_segment",
            entity_id=segment.id,
            snapshot=segment.model_dump(),
            reason=f"Processed Part {segment.segment_index} via {exec_result.provider_name}",
        )

        # Update segment to PROCESSED
        segment.generated_prose = generated_prose.strip()
        segment.status = "processed"
        self.segment_repo.update(segment)

        return exec_result

    def rethink_segment(
        self,
        project_id: str,
        segment_id: str,
        feedback: str = "",
        preferred_provider: Optional[str] = None,
    ) -> ProviderExecutionResult:
        """
        Re-thinks / regenerates the prose for the current segment with author guidance
        WITHOUT re-running or touching previous committed story parts!
        """
        segment = self.segment_repo.get(segment_id)
        if not segment:
            raise ValueError(f"Segment '{segment_id}' not found.")

        # Re-run with custom feedback
        instructions = f"Author Request for Rethink / Revision: {feedback.strip()}" if feedback else "Please rethink and enhance this section."
        return self.process_segment_with_ai(
            project_id=project_id,
            segment_id=segment_id,
            custom_instructions=instructions,
            preferred_provider=preferred_provider,
        )


agentic_rag_service = AgenticRAGService()
