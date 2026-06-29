"""
NeuralSwarm Backend Configuration
Loads settings from environment variables with sensible defaults.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Qwen / DashScope API
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    qwen_base_url: str = os.getenv(
        "QWEN_BASE_URL",
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )
    qwen_model_fast: str = os.getenv("QWEN_MODEL_FAST", "qwen-plus")
    qwen_model_reasoning: str = os.getenv("QWEN_MODEL_REASONING", "qwen-max")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # Sandbox
    sandbox_timeout: int = int(os.getenv("SANDBOX_TIMEOUT", "30"))
    sandbox_max_memory_mb: int = int(os.getenv("SANDBOX_MAX_MEMORY_MB", "512"))

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./debate_logs.db")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
