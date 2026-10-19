"""Google Gemini AI Provider using the official Google GenAI SDK."""

import json
import logging
from typing import Optional, List, Dict, Any, Type, TypeVar
from pydantic import BaseModel, ValidationError

from storybook.config import config
from storybook.providers.base import BaseAIProvider
from storybook.models import (
    StoryDevelopmentResponse,
    OutlineResponse,
    SceneBreakdownResponse,
    SceneProposal,
    StoryBibleExtractionResponse,
    ContinuityReviewResponse,
    SceneRewriteResponse,
)

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini provider using the official modern Google GenAI SDK (`google-genai`).
    Supports structured JSON schema outputs and plain text generation.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (api_key or config.gemini_api_key or "").strip()
        self.model_name = (model_name or config.gemini_model or "gemini-2.5-flash").strip()
        self._client = None

    def _get_client(self):
        """Lazily initialize client to verify credentials on demand."""
        if not self.api_key:
            raise ValueError(
                "Gemini API key is not configured. Please add your key in AI Provider Settings "
                "or define GEMINI_API_KEY in your .env file."
            )
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "The official 'google-genai' SDK is not installed in the environment."
                )
        return self._client

    def get_provider_name(self) -> str:
        return "gemini"

    def get_model_name(self) -> str:
        return self.model_name

    def test_connection(self) -> Dict[str, Any]:
        """Test API connectivity with a minimal prompt."""
        if not self.api_key:
            return {
                "ok": False,
                "provider": "gemini",
                "model": self.model_name,
                "message": "GEMINI_API_KEY is not configured.",
            }
        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents="Hello, please reply with 'OK'.",
            )
            return {
                "ok": True,
                "provider": "gemini",
                "model": self.model_name,
                "message": f"Gemini connection successful: {response.text.strip()[:60]}",
            }
        except Exception as e:
            logger.error(f"Gemini test connection failed: {type(e).__name__}: {e}")
            return {
                "ok": False,
                "provider": "gemini",
                "model": self.model_name,
                "message": f"Gemini connection error: {str(e)}",
            }

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        client = self._get_client()
        try:
            from google.genai import types
            cfg = types.GenerateContentConfig(
                system_instruction=system_instruction
            ) if system_instruction else None

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=cfg,
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemini text generation failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Gemini generation error: {str(e)}") from e

    def _generate_structured(
        self, prompt: str, schema_class: Type[T], system_instruction: Optional[str] = None
    ) -> T:
        """Call Gemini requesting structured JSON and validate against the Pydantic schema."""
        client = self._get_client()
        try:
            from google.genai import types

            config_args = {
                "response_mime_type": "application/json",
                "response_json_schema": schema_class.model_json_schema(),
            }
            if system_instruction:
                config_args["system_instruction"] = system_instruction

            cfg = types.GenerateContentConfig(**config_args)

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=cfg,
            )

            raw_text = (response.text or "").strip()
            # Handle potential markdown code block wrapping
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            return schema_class.model_validate_json(raw_text)
        except ValidationError as ve:
            logger.error(f"Gemini returned invalid structure: {ve}")
            raise ValueError(f"AI response did not match expected structure: {ve}") from ve
        except Exception as e:
            logger.error(f"Gemini structured generation failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Gemini structured generation error: {str(e)}") from e

    def generate_story_development(
        self, premise: str, genre: str, tone: str, audience: str, notes: str
    ) -> StoryDevelopmentResponse:
        system = (
            "You are an expert story architect and development editor. "
            "Develop a rich narrative foundation based on the author's input. "
            "Be creative, identify key themes, character goals, and turning points, "
            "and raise thoughtful clarifying questions if core elements remain underspecified."
        )
        prompt = (
            f"Premise: {premise}\n"
            f"Genre: {genre}\n"
            f"Tone: {tone}\n"
            f"Target Audience: {audience or 'General'}\n"
            f"Additional Notes: {notes or 'None'}\n\n"
            "Develop this into a comprehensive story foundation adhering strictly to the requested schema."
        )
        return self._generate_structured(prompt, StoryDevelopmentResponse, system_instruction=system)

    def generate_outline(
        self, premise: str, synopsis: str, num_chapters: int = 5
    ) -> OutlineResponse:
        system = (
            "You are a master story outliner. Organize the story into a compelling, "
            f"tightly-paced outline of exactly {num_chapters} chapters. "
            "Each chapter must detail title, summary, character arcs, turning points, "
            "important revelations, and setups/payoffs."
        )
        prompt = (
            f"Story Premise: {premise}\n\n"
            f"Story Synopsis:\n{synopsis}\n\n"
            f"Generate a {num_chapters}-chapter outline following the schema."
        )
        return self._generate_structured(prompt, OutlineResponse, system_instruction=system)

    def generate_scene_breakdown(
        self, chapter_title: str, chapter_summary: str, num_scenes: int = 3
    ) -> SceneBreakdownResponse:
        system = (
            "You are a narrative designer breaking chapters into detailed cinematic scenes. "
            f"Break this chapter down into {num_scenes} distinct scenes. For each scene, specify purpose, "
            "POV, location, dramatic conflict, emotional shift, continuity requirements, "
            "and visual/framing notes to support future visual adaptation."
        )
        prompt = (
            f"Chapter Title: {chapter_title}\n"
            f"Chapter Summary: {chapter_summary}\n\n"
            f"Provide a {num_scenes}-scene breakdown."
        )
        return self._generate_structured(prompt, SceneBreakdownResponse, system_instruction=system)

    def draft_scene_prose(
        self, scene: SceneProposal, context: str, instructions: str = ""
    ) -> str:
        system = (
            "You are an accomplished literary fiction writer. Write immersive, evocative prose "
            "for the provided scene that brings characters and environment to life. "
            "Ground the writing in sensory detail and psychological realism."
        )
        prompt = (
            f"Chapter Context:\n{context}\n\n"
            f"Scene Title: {scene.title}\n"
            f"Summary: {scene.summary}\n"
            f"POV: {scene.pov}\n"
            f"Location: {scene.location}\n"
            f"Time: {scene.time_marker}\n"
            f"Characters Present: {', '.join(scene.characters_present)}\n"
            f"Dramatic Conflict: {scene.dramatic_conflict}\n"
            f"Emotional Shift: {scene.emotional_shift}\n"
            f"Special Instructions: {instructions or 'Draft compelling narrative prose.'}\n\n"
            "Draft the complete prose for this scene."
        )
        return self.generate_text(prompt, system_instruction=system)

    def rewrite_scene(
        self, scene_prose: str, instructions: str, tone: str = ""
    ) -> SceneRewriteResponse:
        system = (
            "You are an expert prose stylist and line editor. Rewrite the scene according to "
            "the user's instructions while honoring the established voice and story events."
        )
        prompt = (
            f"Target Tone: {tone or 'Preserve existing tone'}\n"
            f"Instructions: {instructions}\n\n"
            f"Original Prose:\n{scene_prose}\n\n"
            "Provide the rewritten prose and a summary of your changes."
        )
        return self._generate_structured(prompt, SceneRewriteResponse, system_instruction=system)

    def extract_story_bible(self, text: str) -> StoryBibleExtractionResponse:
        system = (
            "You are a narrative continuity expert. Analyze the manuscript text and extract "
            "structured story bible records: major characters, locations, and canonical world facts."
        )
        prompt = (
            f"Analyze the following text and extract characters, locations, and facts:\n\n{text[:12000]}"
        )
        return self._generate_structured(prompt, StoryBibleExtractionResponse, system_instruction=system)

    def review_continuity(
        self, story_bible_facts: List[str], scene_summaries: List[str]
    ) -> ContinuityReviewResponse:
        system = (
            "You are a strict continuity editor. Compare the established canon facts against "
            "the scene summaries. Flag any factual contradictions, timeline conflicts, character knowledge "
            "anachronisms, or sudden unearned motivation shifts."
        )
        prompt = (
            "CANON FACTS:\n" + "\n".join(f"- {f}" for f in story_bible_facts) + "\n\n"
            "SCENE SUMMARIES:\n" + "\n".join(f"- {s}" for s in scene_summaries) + "\n\n"
            "Perform a thorough continuity audit and provide your findings."
        )
        return self._generate_structured(prompt, ContinuityReviewResponse, system_instruction=system)
