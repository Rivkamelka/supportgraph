"""Central settings for SupportGraph.

Everything reads from environment variables (via .env in local dev, or
Docker Compose's `environment:` blocks in the containerised run). The
important design point: leaving LLM_PROVIDER/EMBEDDING_PROVIDER unset (or
set to their defaults) is a fully supported "demo mode" -- the app boots
and answers questions with zero API keys and zero cost, using the mock
chat model and hashing embeddings. Setting a real provider + key is a
one-line change, not a code change (see app/llm/provider.py and
app/llm/embeddings.py).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _blank_env_vars_use_defaults(cls, data: Any) -> Any:
        """Some hosts (Vercel included) pre-create an environment variable
        with an empty string the moment they see its NAME -- e.g. by
        auto-detecting a committed .env/.env.example -- without it ever
        being given a real value. An empty string is not a valid int
        (mysql_port, oracle_port, app_port), so without this it turns
        "no value was actually configured" into a hard crash at import
        time instead of silently falling back to this field's default,
        which is the whole point of demo mode. Treat "" as "not set" for
        every field, not just the int ones, since the same failure mode
        could hit any field type later."""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v != ""}
        return data

    # --- LLM ---
    llm_provider: str = "mock"  # mock | openai | anthropic
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-haiku-latest"

    # --- Embeddings ---
    embedding_provider: str = "hashing"  # hashing | openai

    # --- MySQL ---
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "support_app"
    mysql_password: str = "support_app_pw"
    mysql_database: str = "support_ecommerce"

    # --- MongoDB ---
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_database: str = "supportgraph"

    # --- Oracle ---
    oracle_host: str = "localhost"
    oracle_port: int = 1521
    oracle_service: str = "XEPDB1"
    oracle_user: str = "support_app"
    oracle_password: str = "support_app_pw"

    # --- Qdrant ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "support_policies"

    # --- App ---
    app_port: int = 8000

    @property
    def is_demo_mode(self) -> bool:
        """True when no real LLM key is configured -- i.e. the mock chat
        model will be used regardless of llm_provider's literal value."""
        if self.llm_provider == "openai":
            return not bool(self.openai_api_key)
        if self.llm_provider == "anthropic":
            return not bool(self.anthropic_api_key)
        return True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
