from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    NOTION_API_KEY: str = Field(default_factory=lambda: os.environ.get("NOTION_API_KEY", ""))
    NOTION_DATABASE_ID: str = Field(default_factory=lambda: os.environ.get("NOTION_DATABASE_ID", ""))
    WEBHOOK_API_KEY: str = Field(default_factory=lambda: os.environ.get("WEBHOOK_API_KEY", ""))
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


settings = Settings() 