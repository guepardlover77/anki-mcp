"""Configuration settings for Anki MCP Server."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="ANKI_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # AnkiConnect settings
    host: str = Field(
        default="localhost",
        description="AnkiConnect host",
    )
    port: int = Field(
        default=8765,
        description="AnkiConnect port",
    )
    api_key: str | None = Field(
        default=None,
        description="AnkiConnect API key (if configured)",
    )
    timeout: float = Field(
        default=10.0,
        description="HTTP timeout in seconds for regular operations",
    )
    sync_timeout: float = Field(
        default=60.0,
        description="HTTP timeout in seconds for sync operations",
    )

    # Server settings
    server_name: str = Field(
        default="anki-mcp",
        description="MCP server name",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    @property
    def anki_connect_url(self) -> str:
        """Get the full AnkiConnect URL."""
        return f"http://{self.host}:{self.port}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
