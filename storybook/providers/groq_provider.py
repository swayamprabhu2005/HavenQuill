"""Groq AI Provider using the official Groq SDK."""

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


class GroqProvider(BaseAIProvider):
    """
    Groq AI Provider using the official Groq SDK.
    Supports high-speed LLM inference with JSON mode validation.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (api_key if api_key is not None else (config.groq_api_key or "")).strip()
        self.model_name = (model_name or config.groq_model or "qwen/qwen3.8-27b").strip()
        self._client = None

    def _get_client(self):
        """Lazily initialize Groq client."""
        if not self.api_key:
            raise ValueError(
                "Groq API key is not configured. Please add your key in AI Provider Settings "
                "or define GROQ_API_KEY in your .env file."
            )
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "The official 'groq' SDK is not installed in the environment."
                )
        return self._client

    def get_provider_name(self) -> str:
        return "groq"

    def get_model_name(self) -> str:
        return self.model_name

    def test_connection(self) -> Dict[str, Any]:
        """Test Groq API connectivity with a minimal completion."""
        if not self.api_key:
            return {
                "ok": False,
                "provider": "groq",
                "model": self.model_name,
                "message": "GROQ_API_KEY is not configured.",
            }
        try:
            client = self._get_client()
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": "Reply with 'OK'."}],
                model=self.model_name,
                max_tokens=10,
            )
            reply = chat_completion.choices[0].message.content or ""
            return {
                "ok": True,
                "provider": "groq",
                "model": self.model_name,
                "message": f"Groq connection successful: {reply.strip()}",
            }
        except Exception as e:
            logger.error(f"Groq test connection failed: {type(e).__name__}: {e}")
            return {
                "ok": False,
                "provider": "groq",
                "model": self.model_name,
                "message": f"Groq connection error: {str(e)}",
            }

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        client = self._get_client()
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            completion = client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=0.7,
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Groq text generation failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Groq generation error: {str(e)}") from e

    def _generate_structured(
        self, prompt: str, schema_class: Type[T], system_instruction: Optional[str] = None
    ) -> T:
        """Call Groq with JSON object mode and validate against the Pydantic schema."""
        client = self._get_client()
        schema_json = json.dumps(schema_class.model_json_schema(), indent=2)

        augmented_system = (
            f"{system_instruction or 'You are an expert story development assistant.'}\n"
            f"CRITICAL: You MUST respond with ONLY valid JSON adhering strictly to this JSON Schema:\n"
            f"{schema_json}\n"
            "Do not include any commentary or code fences outside the JSON object."
        )

        messages = [
            {"role": "system", "content": augmented_system},
            {"role": "user", "content": prompt},
        ]

        try:
            completion = client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            raw_text = (completion.choices[0].message.content or "").strip()
            return schema_class.model_validate_json(raw_text)
        except ValidationError as ve:
            logger.error(f"Groq returned invalid structure: {ve}")
            raise ValueError(f"AI response did not match expected structure: {ve}") from ve
        except Exception as e:
            logger.error(f"Groq structured generation failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Groq structured generation error: {str(e)}") from e

    def generate_story_development(
        self, premise: str, genre: str, tone: str, audience: str, notes: str
    ) -> StoryDevelopmentResponse:
        system = "You are a professional narrative architect and developmental editor."
        prompt = (
            f"Premise: {premise}\n"
            f"Genre: {genre}\n"
            f"Tone: {tone}\n"
            f"Target Audience: {audience or 'General'}\n"
            f"Notes: {notes or 'None'}\n\n"
            "Generate complete story development details matching the JSON schema."
        )
        return self._generate_structured(prompt, StoryDevelopmentResponse, system_instruction=system)

    def generate_outline(
        self, premise: str, synopsis: str, num_chapters: int = 5
    ) -> OutlineResponse:
        system = f"You are a master story outliner. Produce a structured {num_chapters}-chapter outline."
        prompt = (
            f"Premise: {premise}\n\n"
            f"Synopsis:\n{synopsis}\n\n"
            f"Generate a {num_chapters}-chapter outline matching the schema."
        )
        return self._generate_structured(prompt, OutlineResponse, system_instruction=system)

    def generate_scene_breakdown(
        self, chapter_title: str, chapter_summary: str, num_scenes: int = 3
    ) -> SceneBreakdownResponse:
        system = f"You are a narrative scene designer. Break this chapter into {num_scenes} rich scenes."
        prompt = (
            f"Chapter: {chapter_title}\n"
            f"Summary: {chapter_summary}\n\n"
            f"Generate {num_scenes} structured scene records matching the schema."
        )
        return self._generate_structured(prompt, SceneBreakdownResponse, system_instruction=system)

    def draft_scene_prose(
        self, scene: SceneProposal, context: str, instructions: str = ""
    ) -> str:
        system = "You are a skilled creative fiction author crafting immersive prose."
        prompt = (
            f"Context:\n{context}\n\n"
            f"Scene: {scene.title}\n"
            f"Summary: {scene.summary}\n"
            f"POV: {scene.pov} | Location: {scene.location} | Time: {scene.time_marker}\n"
            f"Characters: {', '.join(scene.characters_present)}\n"
            f"Conflict: {scene.dramatic_conflict}\n"
            f"Emotional Shift: {scene.emotional_shift}\n"
            f"Instructions: {instructions or 'Write evocative literary prose.'}\n\n"
            "Write the scene prose."
        )
        return self.generate_text(prompt, system_instruction=system)

    def rewrite_scene(
        self, scene_prose: str, instructions: str, tone: str = ""
    ) -> SceneRewriteResponse:
        system = "You are a line editor and rewriting specialist."
        prompt = (
            f"Tone: {tone or 'Preserve tone'}\n"
            f"Instructions: {instructions}\n\n"
            f"Original Prose:\n{scene_prose}\n\n"
            "Provide the rewritten prose and a summary of modifications."
        )
        return self._generate_structured(prompt, SceneRewriteResponse, system_instruction=system)

    def extract_story_bible(self, text: str) -> StoryBibleExtractionResponse:
        system = "You are a story continuity specialist extracting characters, locations, and canon facts."
        prompt = f"Analyze the following excerpt and extract bible records:\n\n{text[:10000]}"
        return self._generate_structured(prompt, StoryBibleExtractionResponse, system_instruction=system)

    def review_continuity(
        self, story_bible_facts: List[str], scene_summaries: List[str]
    ) -> ContinuityReviewResponse:
        system = "You are an eagle-eyed continuity editor identifying narrative inconsistencies."
        prompt = (
            "CANON FACTS:\n" + "\n".join(f"- {f}" for f in story_bible_facts) + "\n\n"
            "SCENE SUMMARIES:\n" + "\n".join(f"- {s}" for s in scene_summaries) + "\n\n"
            "Review consistency and provide your report matching the schema."
        )
        return self._generate_structured(prompt, ContinuityReviewResponse, system_instruction=system)
