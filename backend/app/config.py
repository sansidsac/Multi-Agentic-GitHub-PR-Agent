"""Configuration management for the PR Review Agent"""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    
    LYZR_API_KEY: str
    LYZR_AGENT_ID: str
    LYZR_API_URL: str = "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"
    
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = "INFO"
    
    DEFAULT_USER_ID: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def generate_webhook_secret(self) -> str:
        """Generate a secure webhook secret if not provided"""
        if not self.GITHUB_WEBHOOK_SECRET or self.GITHUB_WEBHOOK_SECRET == "generate_secret_with_script":
            self.GITHUB_WEBHOOK_SECRET = secrets.token_urlsafe(32)
        return self.GITHUB_WEBHOOK_SECRET


settings = Settings()

if not settings.GITHUB_WEBHOOK_SECRET or settings.GITHUB_WEBHOOK_SECRET == "generate_secret_with_script":
    settings.GITHUB_WEBHOOK_SECRET = settings.generate_webhook_secret()
    print(f"\n{'='*80}")
    print(f"🔐 GENERATED WEBHOOK SECRET (Add this to your .env file):")
    print(f"{'='*80}")
    print(f"GITHUB_WEBHOOK_SECRET={settings.GITHUB_WEBHOOK_SECRET}")
    print(f"{'='*80}\n")
