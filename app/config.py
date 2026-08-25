from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    PROJECT_NAME: str = "DocuAgent"
    ENVIRONMENT: str = "production"
    FRONTEND_URL: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/docuagent"

    # LLM (Groq - fast, universal active model)
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "groq/compound-mini"

    # Embeddings (Hugging Face / FastEmbed)
    EMBEDDING_PROVIDER: str = "huggingface"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    HUGGINGFACE_API_KEY: str = ""

    # Uploads (Temporary processing path)
    UPLOAD_DIR: Path = Path("./uploads")

    @property
    def is_dev(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def cors_origins(self) -> list[str]:
        if not self.FRONTEND_URL:
            return ["*"]
        origins = [
            self.FRONTEND_URL.strip().rstrip("/"),
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:5173",
            "http://localhost:3000",
        ]
        return list(dict.fromkeys(origins))


settings = Settings()
