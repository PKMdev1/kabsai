from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/kabs_assistant"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-5"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # AWS S3
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "kabs-assistant-files"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis (optional)
    redis_url: Optional[str] = None
    
    # File storage
    upload_dir: str = "./uploads"
    max_file_size: int = 0  # No limit - unlimited file size
    
    # CORS
    allowed_origins: list = [
        "http://localhost:3000", 
        "http://localhost:3001",
        "https://*.vercel.app",
        "https://*.railway.app"
    ]
    
    class Config:
        env_file = ".env"


settings = Settings()
