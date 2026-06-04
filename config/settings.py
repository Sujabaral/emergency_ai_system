
# config/settings.py

import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    APP_ENV: str = "development"
    DEDUP_WINDOW_SECONDS: int = 300 #for 5min ignore same alert    
    RULES_FILE_PATH: str = str(         # Path to the YAML file
        Path(__file__).parent / "severity_rules.yaml"
    )

    @field_validator("APP_ENV")
    @classmethod
    def env_must_be_valid(cls, value: str) -> str:
        allowed = {"development", "staging", "production"}
        if value not in allowed:
            raise ValueError(
                f"APP_ENV must be one of {allowed}, got: '{value}'"
            )
        return value

    @field_validator("DEDUP_WINDOW_SECONDS")
    @classmethod
    def window_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                f"DEDUP_WINDOW_SECONDS must be > 0, got: {value}"
            )
        return value

    @field_validator("RULES_FILE_PATH")
    @classmethod
    def rules_file_must_exist(cls, value: str) -> str:
        if not Path(value).exists():
            raise ValueError(
                f"RULES_FILE_PATH points to a file that doesn't exist: '{value}'"
            )
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
# creating new Settings() objects all over the place
settings = Settings()
