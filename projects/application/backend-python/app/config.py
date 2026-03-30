from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Server
    PORT: int = 8080

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"

    # Keycloak
    KEYCLOAK_URL: str = "http://localhost:8081"
    KEYCLOAK_REALM: str = "app"
    KEYCLOAK_CLIENT_ID: str = "backend"
    KEYCLOAK_CLIENT_SECRET: str = ""

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:4200"

    # AI
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
