"""Configuration management for the PDF RAG pipeline."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    nomic_api_key: str = Field(default="", env="NOMIC_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    
    # FAISS Configuration
    faiss_index_path: Path = Field(default=Path("./data/faiss_index"), env="FAISS_INDEX_PATH")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    
    # Docling Configuration
    docling_max_pages: int = Field(default=100, env="DOCLING_MAX_PAGES")
    docling_cache_dir: Path = Field(default=Path("./cache"), env="DOCLING_CACHE_DIR")
    
    # Embedding Configuration
    embedding_model: str = Field(default="nomic-embed-text-v1.5", env="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=768, env="EMBEDDING_DIMENSION")
    
    # RAG Configuration
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def setup_directories(self):
        """Create necessary directories."""
        self.faiss_index_path.parent.mkdir(parents=True, exist_ok=True)
        self.docling_cache_dir.mkdir(parents=True, exist_ok=True)
        Path("./data/documents").mkdir(parents=True, exist_ok=True)
        Path("./data/processed").mkdir(parents=True, exist_ok=True)


# Initialize settings
settings = Settings()
settings.setup_directories()