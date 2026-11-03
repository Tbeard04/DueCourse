"""Environment configuration. Every variable is documented in .env.example."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ch_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    duecourse_data_dir: Path = Path("data")
    duecourse_api_token: str = ""
    # Default chosen by the model-selection eval (03-evals/model-selection.md): best measured
    # rubric pass-rate at 2x less than Opus — the config follows the evidence.
    draft_model: str = "claude-sonnet-5-5"
    judge_model: str = "claude-sonnet-5-5"

    @property
    def db_path(self) -> Path:
        return self.duecourse_data_dir / "duecourse.db"

    @property
    def cache_dir(self) -> Path:
        return self.duecourse_data_dir / "cache"

    @property
    def lancedb_dir(self) -> Path:
        return self.duecourse_data_dir / "lancedb"


def get_settings() -> Settings:
    """Fresh settings on every call — cheap, and keeps tests simple (monkeypatch env, done)."""
    return Settings()
