"""Configuration management for the PDF RAG pipeline."""

import os
from pathlib import Path
from typing import List
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

    # LLM Configuration
    llm_provider: str = Field(default="", env="LLM_PROVIDER")  # e.g., 'ollama'
    llm_model: str = Field(default="", env="LLM_MODEL")        # e.g., 'llama3.2'
    
    # Main Solver Configuration
    llm_backend: str = Field(default="ollama", env="LLM_BACKEND")  # "ollama" | "openrouter" | "openai"
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field(default="llama3.1:8b", env="OLLAMA_MODEL")
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openrouter/auto", env="OPENROUTER_MODEL")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    
    # Agent Framework Configuration
    agent_framework: str = Field(default="agentsdk", env="AGENT_FRAMEWORK")  # "agentsdk" | "autogen" | "low-abstraction"
    
    # Resource Bounds Configuration
    max_iterations: int = Field(default=50, env="MAX_ITERATIONS")
    max_depth: int = Field(default=10, env="MAX_DEPTH")
    cost_limit: float = Field(default=10.0, env="COST_LIMIT")  # USD
    time_limit: int = Field(default=3600, env="TIME_LIMIT")  # seconds
    token_limit: int = Field(default=100000, env="TOKEN_LIMIT")
    retry_limit: int = Field(default=3, env="RETRY_LIMIT")
    retry_backoff: float = Field(default=1.0, env="RETRY_BACKOFF")  # seconds
    no_progress_timeout: int = Field(default=300, env="NO_PROGRESS_TIMEOUT")  # seconds
    approval_timeout: int = Field(default=300, env="APPROVAL_TIMEOUT")  # seconds
    
    # Safety and Governance Configuration
    enable_dry_runs: bool = Field(default=True, env="ENABLE_DRY_RUNS")
    enable_rollback: bool = Field(default=True, env="ENABLE_ROLLBACK")
    enable_audit_logging: bool = Field(default=True, env="ENABLE_AUDIT_LOGGING")
    sandbox_mode: bool = Field(default=True, env="SANDBOX_MODE")
    
    # Telemetry Configuration
    enable_telemetry: bool = Field(default=True, env="ENABLE_TELEMETRY")
    telemetry_endpoint: str = Field(default="", env="TELEMETRY_ENDPOINT")
    
    # Checkpoint Configuration
    summary_every_n: int = Field(default=5, env="SUMMARY_EVERY_N")
    checkpoint_events: List[str] = Field(default_factory=lambda: [
        "loop_iteration_start", "goal_selected", "plan_created", 
        "pre_execution", "before_step", "after_step", "post_execution"
    ], env="CHECKPOINT_EVENTS")
    
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