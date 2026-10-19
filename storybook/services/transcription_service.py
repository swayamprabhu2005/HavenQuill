"""Voice capture and audio transcription service with replaceable providers."""

import os
import io
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from storybook.config import config

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Handles speech-to-text transcription via replaceable providers:
    - mock: Offline deterministic transcript
    - groq: Groq Whisper API (whisper-large-v3)
    - gemini: Google GenAI audio transcription
    - none: Manual transcript review only
    """

    def __init__(self):
        self.audio_dir = config.data_dir / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def save_audio_file(self, filename: str, audio_bytes: bytes) -> Path:
        """Save captured audio bytes to local data directory."""
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        target_path = self.audio_dir / safe_filename
        with open(target_path, "wb") as f:
            f.write(audio_bytes)
        return target_path

    def transcribe_audio(
        self, audio_bytes: bytes, filename: str = "recording.wav"
    ) -> Tuple[str, str]:
        """
        Transcribe audio using the configured transcription provider.
        Returns (transcript_text, provider_name).
        """
        provider_name = (config.transcription_provider or "none").lower()
        if not config.enable_cloud_transcription and provider_name in ("groq", "gemini"):
            return (
                "[Cloud Transcription Disabled] Enable cloud transcription in Settings to process audio with AI, "
                "or enter your transcript manually below.",
                "none"
            )

        if provider_name == "mock":
            return self._transcribe_mock(), "mock"
        elif provider_name == "groq":
            return self._transcribe_groq(audio_bytes, filename), "groq"
        elif provider_name == "gemini":
            return self._transcribe_gemini(audio_bytes, filename), "gemini"
        else:
            return (
                "Transcription provider is set to 'none'. You can type or paste your spoken ideas manually here.",
                "none"
            )

    def _transcribe_mock(self) -> str:
        return (
            "[Mock Audio Transcript] 'I was thinking about a clocktower in an ancient European city, "
            "where time has literally frozen for everyone except an apprentice clockmaker named Elena. "
            "She wanders the frozen streets, discovering that people's memories are fading unless she winds "
            "the central pendulum before sunrise.'"
        )

    def _transcribe_groq(self, audio_bytes: bytes, filename: str) -> str:
        if not config.is_groq_configured:
            raise ValueError(
                "Groq API key is missing. Configure GROQ_API_KEY in Settings to use Groq Whisper transcription."
            )

        try:
            from groq import Groq
            client = Groq(api_key=config.groq_api_key)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="text",
            )
            return str(transcription).strip()
        except Exception as e:
            logger.error(f"Groq transcription error: {e}")
            raise RuntimeError(f"Groq speech-to-text failed: {e}") from e

    def _transcribe_gemini(self, audio_bytes: bytes, filename: str) -> str:
        if not config.is_gemini_configured:
            raise ValueError(
                "Gemini API key is missing. Configure GEMINI_API_KEY in Settings to use Gemini audio transcription."
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=config.gemini_api_key)

            # Determine mime type from filename
            mime_type = "audio/wav"
            if filename.lower().endswith(".mp3"):
                mime_type = "audio/mp3"
            elif filename.lower().endswith(".ogg"):
                mime_type = "audio/ogg"
            elif filename.lower().endswith(".m4a"):
                mime_type = "audio/m4a"

            part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

            response = client.models.generate_content(
                model=config.gemini_model,
                contents=[
                    part,
                    "Please provide an accurate, clean, verbatim transcription of this speech. "
                    "Return only the transcribed text without conversational filler or preambles."
                ]
            )
            return (response.text or "").strip()
        except Exception as e:
            logger.error(f"Gemini transcription error: {e}")
            raise RuntimeError(f"Gemini audio transcription failed: {e}") from e


transcription_service = TranscriptionService()
