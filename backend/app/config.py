from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    anthropic_api_key: str = ""
    database_path: Path = BACKEND_DIR / "data" / "job_match.db"
    claude_model: str = "claude-sonnet-5"


settings = Settings()
