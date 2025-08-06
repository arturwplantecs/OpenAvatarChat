"""
Application settings and configuration
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseSettings, Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    
    # API settings
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    max_sessions: int = Field(default=100, description="Maximum concurrent sessions")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    
    # Pipeline configuration file
    pipeline_config_path: str = Field(
        default="config/chat_with_faster_whisper_stable.yaml",
        description="Path to pipeline configuration file"
    )
    
    # Audio settings
    audio_sample_rate: int = Field(default=16000, description="Audio sample rate")
    audio_chunk_size: int = Field(default=1024, description="Audio chunk size")
    max_audio_duration: int = Field(default=30, description="Maximum audio duration in seconds")
    
    # Video settings  
    video_fps: int = Field(default=25, description="Video frame rate")
    video_width: int = Field(default=512, description="Video width")
    video_height: int = Field(default=512, description="Video height")
    
    # Processing settings
    max_text_length: int = Field(default=1000, description="Maximum text input length")
    processing_timeout: int = Field(default=30, description="Processing timeout in seconds")
    
    # Model paths (relative to project root)
    models_dir: str = Field(default="models", description="Models directory")
    logs_dir: str = Field(default="logs", description="Logs directory")
    
    # Security settings
    enable_ssl: bool = Field(default=False, description="Enable SSL")
    ssl_cert_path: str = Field(default="ssl_certs/localhost.crt", description="SSL certificate path")
    ssl_key_path: str = Field(default="ssl_certs/localhost.key", description="SSL key path")
    
    # Performance settings
    workers: int = Field(default=1, description="Number of worker processes")
    max_concurrent_requests: int = Field(default=10, description="Maximum concurrent requests")
    
    class Config:
        env_file = ".env"
        env_prefix = "AVATARCHAT_"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent


def get_pipeline_config_path() -> Path:
    """Get full path to pipeline configuration"""
    settings = get_settings()
    project_root = get_project_root()
    return project_root / settings.pipeline_config_path


def get_models_dir() -> Path:
    """Get full path to models directory"""
    settings = get_settings()
    project_root = get_project_root()
    return project_root / settings.models_dir


def get_logs_dir() -> Path:
    """Get full path to logs directory"""
    settings = get_settings()
    project_root = get_project_root()
    return project_root / settings.logs_dir
