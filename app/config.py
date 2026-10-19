from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Typed view of .env / .env.local (local file overrides)."""

    APP_DEBUG: bool = False
    APP_PROJECT_NAME: str = "lexicon-routing"
    APP_VERSION: str = "0.1.0"

    DATA_DIR: Path = PROJECT_ROOT / "data"

    # NEOS Server (Concorde). The e-mail is required by NEOS; keep it in .env.local.
    NEOS_URL: str = "https://neos-server.org:3333"
    NEOS_EMAIL: str = ""
    NEOS_TIMEOUT_S: int = 1800
    NEOS_INPUT_TYPE: str = "tsplib"       # NEOS Concorde form values: tsplib | xy_l2 | xy_l1
    NEOS_ALGORITHM: str = "cplex"         # cplex (exact, Concorde with CPLEX) | lk (Lin-Kernighan)

    # Large language model used as an alternative preference extractor (Google Gemini API).
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_TIMEOUT_S: int = 120
    GEMINI_THINKING_BUDGET: int = 0     # 0 = answer without a thinking phase; -1 = leave the model's default

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": (".env", ".env.local"), "extra": "ignore"}

    @property
    def source_dir(self) -> Path:
        return self.DATA_DIR / "source"

    @property
    def instances_dir(self) -> Path:
        return self.DATA_DIR / "instances"

    @property
    def corpus_dir(self) -> Path:
        return self.DATA_DIR / "corpus"

    @property
    def lexicon_dir(self) -> Path:
        return self.DATA_DIR / "lexicon"

    @property
    def results_dir(self) -> Path:
        return self.DATA_DIR / "results"


@lru_cache
def get_settings() -> Settings:
    return Settings()
