"""
Application configuration settings
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App settings
    app_name: str = "Travel Guide API"
    debug: bool = True
    
    # LLM settings
    llm_server: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.0-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Search settings
    serper_api_key: str = ""
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

