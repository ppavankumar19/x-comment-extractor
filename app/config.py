from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "X Comment Extractor"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    llm_enabled: bool = True
    llm_backend: Literal["nvidia"] = "nvidia"

    nvidia_api_key: str = ""
    nvidia_model: str = "nvidia/nemotron-3-super-120b-a12b"
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_temperature: float = 1.0
    nvidia_top_p: float = 0.95
    nvidia_max_tokens: int = 16384
    nvidia_reasoning_budget: int = 16384
    nvidia_enable_thinking: bool = True
    nvidia_timeout_seconds: int = 45

    scrape_timeout_ms: int = 120000
    scrape_scroll_pause_ms: int = 2200
    scrape_max_scrolls: int = 120
    scrape_idle_rounds: int = 8
    playwright_headless: bool = True
    x_storage_state_path: str = str(Path("playwright") / "storage_state.json")
    x_login_url: str = "https://x.com/i/flow/login"
    x_auth_token: str = ""
    x_ct0: str = ""
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
    )


    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
