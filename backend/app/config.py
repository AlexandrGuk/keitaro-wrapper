from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    keitaro_base_url: str = ""
    keitaro_api_key: str = ""
    database_url: str = ""
    campaign_prefix: str = "test_guk_"
    app_username: str = ""
    app_password: str = ""
    session_secret: str = ""
    session_https: bool = False

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )

    @field_validator("keitaro_base_url")
    @classmethod
    def strip_url(cls, value: str) -> str:
        return value.strip().rstrip("/")

    @field_validator("keitaro_api_key", "app_username", "app_password", "session_secret")
    @classmethod
    def strip_secret(cls, value: str) -> str:
        return value.strip()

    @field_validator("campaign_prefix")
    @classmethod
    def normalize_prefix(cls, value: str) -> str:
        prefix = value.strip().lower()
        if not prefix.endswith("_"):
            prefix = f"{prefix}_"
        return prefix

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url.strip():
            return self.database_url.strip()
        path = (BACKEND_DIR / "data" / "app.db").as_posix()
        return f"sqlite:///{path}"

    @property
    def frontend_dir(self) -> Path:
        return ROOT_DIR / "frontend"


settings = Settings()
