"""
Application configuration management.
Loads settings from environment variables with .env file support.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import logging


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ----- KSeF Configuration -----
    ksef_environment: str = Field(
        default="test",
        description="KSeF environment: test, demo, or production",
    )
    ksef_api_url: Optional[str] = Field(
        default=None,
        description="Override KSeF API URL",
    )
    company_nip: str = Field(
        default="",
        description="Company NIP (10 digits)",
    )
    ksef_auth_token: str = Field(
        default="",
        description="KSeF authorization token",
    )

    # ----- Certificate Authentication -----
    certificate_path: Optional[str] = Field(
        default=None,
        description="Path to certificate PEM file",
    )
    private_key_path: Optional[str] = Field(
        default=None,
        description="Path to private key PEM file",
    )
    private_key_password: Optional[str] = Field(
        default=None,
        description="Private key password",
    )

    # ----- Application Settings -----
    app_name: str = Field(default="mikroKSeF")
    debug: bool = Field(default=True)
    backend_url: str = Field(default="http://localhost:8000")
    frontend_url: str = Field(default="http://localhost:3000")
    cors_origins: str = Field(default="http://localhost:3000")

    # ----- Session Settings -----
    session_timeout_minutes: int = Field(default=60, ge=1, le=480)

    # ----- Database -----
    database_url: str = Field(default="sqlite:///./mikroksef.db")

    # ----- Security -----
    secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=60)

    # ----- Logging -----
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @field_validator("company_nip")
    @classmethod
    def validate_nip(cls, v: str) -> str:
        """Validate NIP format (10 digits)."""
        if v and len(v.replace("-", "").replace(" ", "")) != 10:
            raise ValueError("NIP must be 10 digits")
        return v.replace("-", "").replace(" ", "")

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def effective_ksef_url(self) -> str:
        """Get the effective KSeF API URL based on environment."""
        if self.ksef_api_url:
            return self.ksef_api_url

        urls = {
            "test": "https://ksef-test.mf.gov.pl/api",
            "demo": "https://ksef-demo.mf.gov.pl/api",
            "production": "https://ksef.mf.gov.pl/api",
        }
        return urls.get(self.ksef_environment, urls["test"])

    def configure_logging(self) -> None:
        """Configure application logging."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.configure_logging()
    return settings
