"""Regression tests for the empty-env-var crash that took down the first
production deploy on Vercel: it auto-detected .env.example and created
real environment variables with an empty string value, which pydantic
rejected as an invalid int. See docs/adr/0005-production-hardening.md."""

from __future__ import annotations

from app.config import Settings


def test_empty_string_env_vars_fall_back_to_defaults(monkeypatch):
    monkeypatch.setenv("MYSQL_PORT", "")
    monkeypatch.setenv("ORACLE_PORT", "")
    monkeypatch.setenv("APP_PORT", "")

    settings = Settings()

    assert settings.mysql_port == 3306
    assert settings.oracle_port == 1521
    assert settings.app_port == 8000


def test_empty_string_env_var_falls_back_for_string_fields_too(monkeypatch):
    monkeypatch.setenv("MYSQL_HOST", "")

    settings = Settings()

    assert settings.mysql_host == "localhost"


def test_real_env_vars_are_still_respected(monkeypatch):
    monkeypatch.setenv("MYSQL_PORT", "9999")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    settings = Settings()

    assert settings.mysql_port == 9999
    assert settings.llm_provider == "openai"
    assert settings.is_demo_mode is False


def test_is_demo_mode_true_without_a_key_even_if_provider_is_set(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = Settings()

    assert settings.is_demo_mode is True
