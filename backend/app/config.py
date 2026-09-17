from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import model_validator


class Settings(BaseSettings):
    APP_ENV: Literal["development", "production", "test"] = "development"
    SECRET_KEY: str = "default-insecure-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "default-insecure-jwt-key-change-in-production"
    DATABASE_URL: str = "sqlite:///./test.db"

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        if self.APP_ENV == "production":
            if len(self.SECRET_KEY) < 32 or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("Secret keys must be at least 32 characters in production.")
        # Fix for Render providing 'postgres://' instead of 'postgresql://'
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return self


settings = Settings()
