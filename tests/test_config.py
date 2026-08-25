from app.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(
        PROJECT_NAME="DocuAgent",
        ENVIRONMENT="development",
        LLM_PROVIDER="groq",
        GROQ_MODEL="llama-3.3-70b-versatile",
        EMBEDDING_PROVIDER="huggingface",
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        EMBEDDING_DIMENSION=384,
    )
    assert settings.PROJECT_NAME == "DocuAgent"
    assert settings.is_dev is True
    assert settings.LLM_PROVIDER == "groq"
    assert settings.EMBEDDING_DIMENSION == 384


def test_settings_production_mode() -> None:
    settings = Settings(ENVIRONMENT="production")
    assert settings.is_dev is False
