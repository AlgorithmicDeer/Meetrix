"""
Configuration management using pydantic-settings.
All environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Ollama connection
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    
    # Model overrides (all default to llama3.2)
    CLASSIFIER_MODEL: str = "llama3.2"
    DECISION_EXTRACTION_MODEL: str = "llama3.2"
    MEETING_HEALTH_MODEL: str = "llama3.2"
    ACTION_ITEM_MODEL: str = "llama3.2"
    ROOT_CAUSE_MODEL: str = "llama3.2"
    RECOMMENDATION_MODEL: str = "llama3.2"
    INTERVENTION_MODEL: str = "llama3.2"
    REPORT_GENERATION_MODEL: str = "llama3.2"
    INSIGHT_QUERY_MODEL: str = "llama3.2"
    SCHEDULER_MODEL: str = "llama3.2"
    UPCOMING_RISK_MODEL: str = "llama3.2"
    
    # Cost configuration
    DEFAULT_HOURLY_RATE: float = 75.0
    
    # Dimension weights (must sum to 1.0)
    WEIGHT_COST: float = 0.25
    WEIGHT_DECISION: float = 0.40
    WEIGHT_PARTICIPATION: float = 0.20
    WEIGHT_RECURRENCE: float = 0.15

    # Waste thresholds
    HIGH_WASTE_THRESHOLD: float = 0.50
    MEDIUM_WASTE_THRESHOLD: float = 0.30
    
    # Timeouts
    LLM_TIMEOUT_SECONDS: int = 120
    REPORT_TIMEOUT_SECONDS: int = 180
    PARALLEL_STAGE_TIMEOUT_SECONDS: int = 300
    
    # Infrastructure
    DATABASE_PATH: str = "/app/data/meetrix.db"
    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8000
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

# Made with Bob
