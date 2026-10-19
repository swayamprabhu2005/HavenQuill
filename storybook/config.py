"""Configuration management for Storybook Studio."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, dotenv_values

# Base directory for the application
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
ENV_EXAMPLE = BASE_DIR / ".env.example"

# Load environment variables on import
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)
else:
    load_dotenv(override=True)


class AppConfig:
    """Manages application settings, AI provider configs, and paths."""

    def __init__(self, env_path: Optional[Path] = None):
        self.env_path = env_path or ENV_FILE
        self.reload()

    def reload(self) -> None:
        """Reload configuration from disk and environment."""
        if self.env_path.exists():
            load_dotenv(dotenv_path=self.env_path, override=True)

        self.app_env: str = os.getenv("APP_ENV", "development")
        self.app_name: str = os.getenv("APP_NAME", "Storybook Studio")
        self.data_dir_str: str = os.getenv("APP_DATA_DIR", "./data")
        self.data_dir: Path = (BASE_DIR / self.data_dir_str).resolve() if not Path(self.data_dir_str).is_absolute() else Path(self.data_dir_str)

        self.ai_provider: str = os.getenv("AI_PROVIDER", "mock").lower()
        self.ai_auto_fallback: bool = os.getenv("AI_AUTO_FALLBACK", "false").lower() in ("true", "1", "yes")

        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

        self.enable_cloud_transcription: bool = os.getenv("ENABLE_CLOUD_TRANSCRIPTION", "false").lower() in ("true", "1", "yes")
        self.transcription_provider: str = os.getenv("TRANSCRIPTION_PROVIDER", "none").lower().strip()

        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

        # Ensure runtime data directories exist
        self.ensure_data_directories()

    def ensure_data_directories(self) -> None:
        """Create data and temporary directories if they do not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "backups").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "exports").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "audio").mkdir(parents=True, exist_ok=True)

    @property
    def db_path(self) -> Path:
        """Path to the SQLite database file."""
        return self.data_dir / "storybook.db"

    @property
    def is_gemini_configured(self) -> bool:
        """Check if Gemini API key is provided."""
        return bool(self.gemini_api_key and len(self.gemini_api_key) > 5)

    @property
    def is_groq_configured(self) -> bool:
        """Check if Groq API key is provided."""
        return bool(self.groq_api_key and len(self.groq_api_key) > 5)

    @staticmethod
    def mask_key(key: Optional[str]) -> str:
        """Safely mask an API key for display without exposing the secret."""
        if not key or len(key.strip()) < 8:
            return "[Not Configured]"
        cleaned = key.strip()
        return f"{cleaned[:4]}...{cleaned[-4:]}"

    def update_settings(self, updates: Dict[str, Any]) -> None:
        """
        Safely update .env settings on disk without discarding existing comments or keys.
        """
        # Read current lines or initialize from example if empty
        lines = []
        if self.env_path.exists():
            with open(self.env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        elif ENV_EXAMPLE.exists():
            with open(ENV_EXAMPLE, "r", encoding="utf-8") as f:
                lines = f.readlines()

        existing_keys = set()
        new_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                existing_keys.add(key)
                if key in updates:
                    val = str(updates[key])
                    new_lines.append(f"{key}={val}\n")
                    continue
            new_lines.append(line if line.endswith("\n") else line + "\n")

        # Append any new keys not already in the file
        for k, v in updates.items():
            if k not in existing_keys:
                new_lines.append(f"{k}={v}\n")

        with open(self.env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        # Reload into current process
        self.reload()


# Singleton config instance
config = AppConfig()
