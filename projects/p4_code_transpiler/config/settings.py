"""
Runtime Configuration Settings for Project 4: High-Performance Code Transpiler
Loads environment variables using pydantic-settings with fallbacks.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORAGE_DIR = PROJECT_ROOT / "storage"
TEMP_PY_DIR = STORAGE_DIR / "temp_py"
TEMP_CPP_DIR = STORAGE_DIR / "temp_cpp"
BINARIES_DIR = STORAGE_DIR / "binaries"

# Ensure runtime directories exist
TEMP_PY_DIR.mkdir(parents=True, exist_ok=True)
TEMP_CPP_DIR.mkdir(parents=True, exist_ok=True)
BINARIES_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Application settings and LLM/compiler configurations."""
    
    # LLM Settings
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.deepseek.com", alias="OPENAI_BASE_URL")
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")

    # Compiler Settings
    cxx_compiler: str = Field(default="g++", alias="CXX_COMPILER")
    default_opt_level: str = Field(default="O3", alias="DEFAULT_OPT_LEVEL")
    execution_timeout_seconds: int = Field(default=15, alias="EXECUTION_TIMEOUT_SECONDS")
    enable_openmp: bool = Field(default=True, alias="ENABLE_OPENMP")

    # Paths
    project_root: Path = PROJECT_ROOT
    storage_dir: Path = STORAGE_DIR
    temp_py_dir: Path = TEMP_PY_DIR
    temp_cpp_dir: Path = TEMP_CPP_DIR
    binaries_dir: Path = BINARIES_DIR

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
