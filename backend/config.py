"""
Configuration module for the Insurance Chatbot backend.

This module uses Pydantic BaseSettings to manage application configuration
from environment variables with sensible defaults for local development.

To set environment variables:
- On Linux/Mac: export OPENAI_API_KEY="your-key-here"
- On Windows: set OPENAI_API_KEY=your-key-here
- Or create a .env file in the backend directory (requires python-dotenv)
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables.
    For local development without API keys, defaults are provided.
    """
    
    # OpenAI API Configuration
    # Note: For local development without OpenAI, we'll use local models
    OPENAI_API_KEY: Optional[str] = None
    
    # Embedding model configuration
    # Using sentence-transformers for local embeddings (no API key needed)
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # LLM model configuration
    # Options: "mock-llm", "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"
    LLM_MODEL_NAME: str = "gpt-4"  # Using GPT-4 for production
    LLM_TEMPERATURE: float = 0.0  # Low temperature for factual, non-hallucinating responses
    
    # STT (Speech-to-Text) Configuration
    # Auto-detect: Use Whisper if OpenAI API key is available, otherwise use mock
    STT_PROVIDER: str = "auto"  # Options: "auto", "mock", "openai-whisper", "google-speech"
    STT_API_KEY: Optional[str] = None
    
    # TTS (Text-to-Speech) Configuration
    TTS_PROVIDER: str = "mock"  # Options: "mock", "amazon-polly", "google-tts"
    TTS_API_KEY: Optional[str] = None
    TTS_REGION: Optional[str] = None  # For AWS Polly
    
    # RAG Configuration
    CHUNK_SIZE: int = 500  # Characters per chunk (with overlap)
    CHUNK_OVERLAP: int = 50  # Overlap between chunks to preserve context
    RETRIEVAL_K: int = 5  # Number of top chunks to retrieve
    
    # Vector Store Configuration
    VECTOR_STORE_PATH: str = "data/vector_store"
    FAISS_INDEX_NAME: str = "policy_index"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Audio file storage
    AUDIO_OUTPUT_DIR: str = "data/audio_output"
    TEMP_UPLOAD_DIR: str = "data/temp_uploads"
    
    class Config:
        """Pydantic config for loading from .env file."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

