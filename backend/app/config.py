
"""Application settings, loaded from environment variables / .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the backend directory containing the .env file.
BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./resume_screening.db"

    # Uploads
    upload_dir: str = "./uploaded_resumes"

    # SMTP / email notifications
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_ssl: bool = False

    # CORS
    cors_origins: str = "*"

    # Matching weights
    tfidf_weight: float = 0.5
    skill_weight: float = 0.5

    # Duplicate detection
    duplicate_shingle_size: int = 5
    duplicate_similarity_threshold: float = 0.6

    # Misc
    api_title: str = "AI Resume Screening and Recruitment Platform"


settings = Settings()
