from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json

class Settings(BaseSettings):
    APP_NAME: str = "PackWise API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    FRONTEND_ORIGINS: str = "[\"http://localhost:3000\"]"
    
    # Placeholders for future subsystems
    DATABASE_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def frontend_origins_list(self) -> List[str]:
        try:
            return json.loads(self.FRONTEND_ORIGINS)
        except Exception:
            return ["http://localhost:3000"]

settings = Settings()
