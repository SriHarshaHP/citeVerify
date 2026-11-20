import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

is_serverless = bool(
    os.getenv("VERCEL")
    or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    or os.getenv("LAMBDA_TASK_ROOT")
)

default_cache_dir = "/tmp/.cache" if is_serverless else "./.cache"
default_db_path = "/tmp/citeverify.db" if is_serverless else "./citeverify.db"

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
    CACHE_DIR: str = default_cache_dir
    DB_PATH: str = default_db_path
    
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

# Ensure directories exist safely (supporting read-only serverless filesystems)
try:
    Path(settings.CACHE_DIR).mkdir(parents=True, exist_ok=True)
except OSError:
    settings.CACHE_DIR = "/tmp/.cache"
    settings.DB_PATH = "/tmp/citeverify.db"
    try:
        Path(settings.CACHE_DIR).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
