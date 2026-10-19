"""Base AI Provider interface for Storybook Studio."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from storybook.models import (
    StoryDevelopmentResponse,
    OutlineResponse,
    SceneBreakdownResponse,
    SceneProposal,
    StoryBibleExtractionResponse,
    ContinuityReviewResponse,
    SceneRewriteResponse,
)


class BaseAIProvider(ABC):
    """Abstract base class for all AI providers."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the canonical name of the provider."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Returns the currently configured model identifier."""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test API connectivity and credentials. Returns a status dict."""
        pass

    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate raw text from a prompt."""
        pass

    @abstractmethod
    def generate_story_development(
        self, premise: str, genre: str, tone: str, audience: str, notes: str
    ) -> StoryDevelopmentResponse:
        """Generate structured story development packet (synopsis, logline, themes, etc.)."""
        pass

    @abstractmethod
    def generate_outline(
        self, premise: str, synopsis: str, num_chapters: int = 5
    ) -> OutlineResponse:
        """Generate a structured multi-chapter outline with character arcs and turning points."""
        pass

    @abstractmethod
    def generate_scene_breakdown(
        self, chapter_title: str, chapter_summary: str, num_scenes: int = 3
    ) -> SceneBreakdownResponse:
        """Generate structured scene proposals for a chapter, including future image metadata."""
        pass

    @abstractmethod
    def draft_scene_prose(
        self, scene: SceneProposal, context: str, instructions: str = ""
    ) -> str:
        """Draft prose for an approved scene proposal."""
        pass

    @abstractmethod
    def rewrite_scene(
        self, scene_prose: str, instructions: str, tone: str = ""
    ) -> SceneRewriteResponse:
        """Rewrite or refine scene prose according to specific instructions."""
        pass

    @abstractmethod
    def extract_story_bible(self, text: str) -> StoryBibleExtractionResponse:
        """Extract characters, locations, and canon facts from source text."""
        pass

    @abstractmethod
    def review_continuity(
        self, story_bible_facts: List[str], scene_summaries: List[str]
    ) -> ContinuityReviewResponse:
        """Review consistency across canon facts and scene summaries."""
        pass
