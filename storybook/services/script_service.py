"""Screenplay and Script Adaptation Service for HavenQuill."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch

from storybook.models import Script, Chapter, Project
from storybook.repositories import (
    ScriptRepository,
    ChapterRepository,
    ProjectRepository,
    SceneRepository,
    VersionHistoryRepository,
)
from storybook.providers.provider_manager import provider_manager, ProviderExecutionResult
from storybook.config import config

logger = logging.getLogger(__name__)


class ScriptService:
    """
    Manages transformation of book chapters into industry-standard screenplays / scripts.
    Tracks which chapters have been adapted, supporting incremental continuation:
    when the author writes the next half of the book, sends both the existing script
    and the new chapters to generate the complete unified screenplay.
    """

    def __init__(
        self,
        script_repo: Optional[ScriptRepository] = None,
        chapter_repo: Optional[ChapterRepository] = None,
        project_repo: Optional[ProjectRepository] = None,
        scene_repo: Optional[SceneRepository] = None,
        version_repo: Optional[VersionHistoryRepository] = None,
    ):
        self.script_repo = script_repo or ScriptRepository()
        self.chapter_repo = chapter_repo or ChapterRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.scene_repo = scene_repo or SceneRepository()
        self.version_repo = version_repo or VersionHistoryRepository()

    def get_or_create_script(self, project_id: str, title: str = "Screenplay Adaptation") -> Script:
        """Fetch the current script for a project or create a blank one."""
        existing = self.script_repo.get_by_project(project_id)
        if existing:
            return existing

        new_script = Script(
            project_id=project_id,
            title=title,
            script_content="",
            covered_chapters_json=[],
            last_chapter_index=0,
        )
        return self.script_repo.create(new_script)

    def get_chapter_coverage_status(self, project_id: str) -> Dict[str, Any]:
        """
        Calculates which chapters are covered in the existing script vs pending adaptation.
        Returns:
            {
                "total_chapters": int,
                "covered_chapters": List[Chapter],
                "pending_chapters": List[Chapter],
                "has_script": bool,
                "is_up_to_date": bool,
            }
        """
        all_chapters = self.chapter_repo.list_by_project(project_id)
        script = self.script_repo.get_by_project(project_id)

        if not script or not script.covered_chapters_json:
            return {
                "total_chapters": len(all_chapters),
                "covered_chapters": [],
                "pending_chapters": all_chapters,
                "has_script": bool(script and script.script_content.strip()),
                "is_up_to_date": False if all_chapters else True,
            }

        covered_ids = set(script.covered_chapters_json)
        covered = [c for c in all_chapters if c.id in covered_ids]
        pending = [c for c in all_chapters if c.id not in covered_ids]

        return {
            "total_chapters": len(all_chapters),
            "covered_chapters": covered,
            "pending_chapters": pending,
            "has_script": bool(script.script_content.strip()),
            "is_up_to_date": len(pending) == 0 and len(all_chapters) > 0,
        }

    def convert_chapters_to_markdown(self, chapters: List[Chapter]) -> str:
        """Converts chapters and their scenes into structured Markdown for AI consumption."""
        md_lines = []
        for ch in chapters:
            md_lines.append(f"# Chapter {ch.order_index}: {ch.title}\n")
            if ch.summary:
                md_lines.append(f"> **Chapter Synopsis**: {ch.summary}\n")

            scenes = self.scene_repo.list_by_chapter(ch.id)
            if scenes:
                for sc in scenes:
                    location_marker = f" [{sc.location}]" if sc.location else ""
                    time_marker = f" - {sc.time_of_day}" if sc.time_of_day else ""
                    md_lines.append(f"### Scene {sc.order_index}: {sc.title}{location_marker}{time_marker}\n")
                    if sc.characters_present:
                        md_lines.append(f"*Characters: {', '.join(sc.characters_present)}*\n")
                    if sc.prose:
                        md_lines.append(f"{sc.prose.strip()}\n")
                    elif sc.summary:
                        md_lines.append(f"{sc.summary.strip()}\n")
            elif getattr(ch, "prose", None):
                md_lines.append(f"{ch.prose.strip()}\n")

            md_lines.append("\n---\n")

        return "\n".join(md_lines).strip()

    def adapt_book_to_script(
        self,
        project_id: str,
        regenerate_all: bool = False,
        custom_instructions: str = "",
        preferred_provider: Optional[str] = None,
    ) -> Tuple[Script, ProviderExecutionResult]:
        """
        Transforms the book into a screenplay.
        If an existing script exists and only new chapters need conversion,
        passes both the existing script and the new chapters to generate seamless continuity.
        """
        project = self.project_repo.get(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        script = self.get_or_create_script(project_id, title=f"{project.title} - Screenplay")
        coverage = self.get_chapter_coverage_status(project_id)

        all_chapters = self.chapter_repo.list_by_project(project_id)
        if not all_chapters:
            raise ValueError("No chapters exist in this project yet. Please create or generate chapters first.")

        # Determine if doing initial full adaptation or continuation
        is_incremental = (
            not regenerate_all
            and coverage["has_script"]
            and len(coverage["pending_chapters"]) > 0
            and len(coverage["covered_chapters"]) > 0
        )

        system_instruction = (
            "You are a veteran Hollywood screenwriter, script doctor, and screenplay adaptation specialist. "
            "Your task is to adapt novel / book prose into an industry-standard screenplay format (standard script style).\n\n"
            "SCREENPLAY FORMAT RULES:\n"
            "1. Scene Headings (Sluglines): All-caps on their own line, e.g.:\n"
            "   INT. OLD OBSERVATORY - NIGHT\n"
            "   EXT. ANCIENT RUINS - DUSK\n"
            "2. Action Lines: Present tense, visually evocative, economical, descriptions of camera-visible action.\n"
            "3. Character Names: Centered in ALL CAPS before speaking, e.g.:\n"
            "   ELENA\n"
            "4. Parentheticals: Under character name, e.g.:\n"
            "   (whispering, trembling)\n"
            "5. Dialogue: Natural, subtext-rich, faithful to the characters' voice and the novel's dramatic beats.\n"
            "6. Transitions: Use sparingly (CUT TO:, FADE IN:, FADE OUT:).\n"
            "7. Return ONLY the screenplay text without meta-commentary or conversational filler."
        )

        if is_incremental:
            # Incremental continuation mode:
            # We send existing script + new chapters to Gemini/Groq
            pending_md = self.convert_chapters_to_markdown(coverage["pending_chapters"])
            prompt = (
                f"PROJECT: {project.title} (Genre: {project.genre} | Tone: {project.tone})\n\n"
                f"EXISTING SCREENPLAY (Adapted from Chapters 1 to {len(coverage['covered_chapters'])}):\n"
                f"\"\"\"\n{script.script_content.strip()}\n\"\"\"\n\n"
                f"NEW BOOK CHAPTERS (Chapters {len(coverage['covered_chapters']) + 1} to {len(all_chapters)}):\n"
                f"\"\"\"\n{pending_md}\n\"\"\"\n\n"
                "TASK:\n"
                "Seamlessly continue the screenplay adaptation for the NEW book chapters.\n"
                "- Match the exact formatting, tone, character voices, and slugline conventions of the existing screenplay.\n"
                "- Pick up immediately from the final scene of the existing script.\n"
                "- Output the COMPLETE updated screenplay containing both the previous parts and the newly adapted scenes united together."
            )
            if custom_instructions:
                prompt += f"\nSPECIAL ADAPTATION NOTES: {custom_instructions.strip()}\n"
        else:
            # Full adaptation mode
            all_md = self.convert_chapters_to_markdown(all_chapters)
            prompt = (
                f"PROJECT: {project.title}\n"
                f"Genre: {project.genre} | Tone: {project.tone}\n"
                f"Premise: {project.premise}\n\n"
                f"BOOK MANUSCRIPT (Full Book Chapters in Markdown):\n"
                f"\"\"\"\n{all_md}\n\"\"\"\n\n"
                "TASK:\n"
                "Adapt the entire book manuscript into a professional, cohesive screenplay.\n"
                "Structure it into cinematic scenes with proper sluglines, character dialogue, and visual action lines."
            )
            if custom_instructions:
                prompt += f"\nSPECIAL ADAPTATION NOTES: {custom_instructions.strip()}\n"

        def _run(provider):
            return provider.generate_text(prompt, system_instruction=system_instruction)

        exec_result = provider_manager.execute_with_fallback(
            operation_name="adapt_book_to_script",
            func=_run,
            preferred_provider=preferred_provider,
        )

        adapted_text: str = exec_result.data

        # Record version snapshot
        self.version_repo.record_snapshot(
            entity_type="script",
            entity_id=script.id,
            snapshot=script.model_dump(),
            reason=f"Script adaptation via {exec_result.provider_name} (incremental={is_incremental})",
        )

        # Update script in database
        script.script_content = adapted_text.strip()
        script.covered_chapters_json = [c.id for c in all_chapters]
        script.last_chapter_index = len(all_chapters)
        updated_script = self.script_repo.update(script)

        return updated_script, exec_result

    def export_script_pdf(self, script: Script, output_path: Path) -> Path:
        """Generates an industry-standard Courier screenplay PDF using ReportLab."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=1.5 * inch,
            rightMargin=1.0 * inch,
            topMargin=1.0 * inch,
            bottomMargin=1.0 * inch,
        )

        styles = getSampleStyleSheet()

        # Screenplay typography
        title_style = ParagraphStyle(
            "ScriptTitle",
            parent=styles["Normal"],
            fontName="Courier-Bold",
            fontSize=16,
            leading=20,
            alignment=1,  # Center
            spaceAfter=24,
        )
        slug_style = ParagraphStyle(
            "ScriptSlug",
            parent=styles["Normal"],
            fontName="Courier-Bold",
            fontSize=10,
            leading=14,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True,
        )
        action_style = ParagraphStyle(
            "ScriptAction",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=10,
            leading=14,
            spaceAfter=8,
        )
        char_style = ParagraphStyle(
            "ScriptChar",
            parent=styles["Normal"],
            fontName="Courier-Bold",
            fontSize=10,
            leading=14,
            leftIndent=1.5 * inch,
            spaceBefore=8,
            spaceAfter=2,
            keepWithNext=True,
        )
        dialogue_style = ParagraphStyle(
            "ScriptDialogue",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=10,
            leading=14,
            leftIndent=0.8 * inch,
            rightIndent=0.8 * inch,
            spaceAfter=8,
        )
        paren_style = ParagraphStyle(
            "ScriptParen",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=10,
            leading=14,
            leftIndent=1.1 * inch,
            rightIndent=1.0 * inch,
            spaceAfter=2,
            keepWithNext=True,
        )

        story = []
        story.append(Paragraph(script.title.upper(), title_style))
        story.append(Spacer(1, 16))

        for raw_line in script.script_content.splitlines():
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 8))
                continue

            # Classify line by standard script markers
            if line.startswith("INT.") or line.startswith("EXT.") or line.startswith("INT/EXT."):
                story.append(Paragraph(line.upper(), slug_style))
            elif line.startswith("(") and line.endswith(")"):
                story.append(Paragraph(line, paren_style))
            elif line.isupper() and len(line) < 35 and not line.endswith("."):
                story.append(Paragraph(line, char_style))
            elif line.startswith("CUT TO:") or line.startswith("FADE OUT:") or line.startswith("FADE IN:"):
                story.append(Paragraph(line, slug_style))
            else:
                story.append(Paragraph(line, action_style))

        doc.build(story)
        return output_path

    def export_script_fountain(self, script: Script) -> str:
        """Returns standard Fountain screenplay format."""
        header = f"Title: {script.title}\nCredit: Screenplay adapted via HavenQuill\nDraft date: {datetime.utcnow().strftime('%B %d, %Y')}\n\n===\n\n"
        return header + script.script_content


script_service = ScriptService()
