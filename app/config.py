import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "CiteVerify"
    DEBUG: bool = True
    PORT: int = 8000
    
    # LLM Settings
    LLM_PROVIDER: str = "offline_mock"  # gemini, openai, anthropic, offline_mock
    LLM_API_KEY: str = ""
    LLM_MODEL_STRONG: str = "gemini-1.5-pro"
    LLM_MODEL_FAST: str = "gemini-1.5-flash"
    
    # Offline Demo and Cache
    OFFLINE_DEMO: bool = True
    CACHE_DIR: str = "./.cache"
    DB_PATH: str = "./citeverify.db"
    
    # Scholarly APIs
    SCHOLARLY_CONTACT_EMAIL: str = "citeverify-demo@innovedge2026.org"
    OPENALEX_API_KEY: str = ""
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    
    # Thresholds
    TITLE_SIMILARITY_THRESHOLD: float = 80.0
    OUTDATED_YEARS_THRESHOLD: int = 10
    SCORE_REVIEW_THRESHOLD: float = 0.50
    ABSTRACT_SCORE_CAP: float = 0.60
    METADATA_SCORE_CAP: float = 0.40
    MAX_PDF_DOWNLOAD_BYTES: int = 15 * 1024 * 1024  # 15 MB
    REQUEST_TIMEOUT_SECONDS: int = 10
    MAX_CONCURRENT_WORKERS: int = 5

settings = Settings()

# Ensure directories exist
Path(settings.CACHE_DIR).mkdir(parents=True, exist_ok=True)
