"""
Configuration Management
Loads environment variables and provides them to the application.
"""

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# 1. Load the .env file explicitly
# This looks for .env in the current working directory (project root)
load_dotenv()

class Settings(BaseSettings):
    # LLM Configuration
    # We use os.getenv with a default "fake-key" so the app starts 
    # even if you don't have a real key yet.
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "sk-fake-key-123")
    
    # Vector DB Configuration
    VECTOR_DB_PATH: str = "./data/chroma_db"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

# Singleton instance
settings = Settings()