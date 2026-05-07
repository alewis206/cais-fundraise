from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Phase 1
    anthropic_api_key: Optional[str] = None
    google_sheet_id: Optional[str] = None
    google_service_account_json_path: Path = Path("./secrets/google-sa.json")
    db_path: Path = Path("./data/prospects.db")
    classifier_default_model: str = "claude-sonnet-4-6"
    classifier_tier1_model: str = "claude-opus-4-7"
    cost_ceiling_usd: float = Field(default=50.0, ge=0)

    # Phase 2
    apollo_api_key: Optional[str] = None
    hunter_api_key: Optional[str] = None
    enrichment_cache_days: int = Field(default=30, ge=1)

    # Phase 3
    crunchbase_api_key: Optional[str] = None
    twitter_bearer_token: Optional[str] = None

    log_level: str = "INFO"

    # Repo-relative paths used by adapters / migrations.
    repo_root: Path = Path(__file__).resolve().parent.parent
    sources_config_path: Path = Path("./config/sources.yaml")
    investor_profile_path: Path = Path("./config/investor_profile.yaml")
    classifier_prompt_path: Path = Path("./prompts/classifier.md")
    migrations_dir: Path = Path("./src/migrations")


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
