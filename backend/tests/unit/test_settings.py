import pytest

from app.core.config import ConfigError, load_settings

BASE = {"DATABASE_URL": "postgresql+psycopg://x:y@localhost/db", "QDRANT_URL": "http://localhost:6333", "APP_SECRET_KEY": "k"}


def _clear_env(monkeypatch):
    for k in ("DATABASE_URL", "QDRANT_URL", "APP_SECRET_KEY", "LLM_PROVIDER", "EMBEDDING_PROVIDER", "LLM_USE_FAKE", "APP_ENV"):
        monkeypatch.delenv(k, raising=False)


def test_missing_required_vars_are_all_listed(monkeypatch):
    _clear_env(monkeypatch)
    with pytest.raises(ConfigError) as exc:
        load_settings(_env_file=None)
    msg = str(exc.value)
    for name in ("DATABASE_URL", "QDRANT_URL", "APP_SECRET_KEY"):
        assert name in msg


def test_valid_settings_load(monkeypatch):
    _clear_env(monkeypatch)
    s = load_settings(_env_file=None, **BASE)
    assert s.LLM_PROVIDER == "qwen"
    assert s.EMBEDDING_DIMENSION == 384
    assert not s.llm_configured


def test_rejects_other_llm_provider(monkeypatch):
    _clear_env(monkeypatch)
    with pytest.raises(ConfigError) as exc:
        load_settings(_env_file=None, LLM_PROVIDER="openai", **BASE)
    assert "LLM_PROVIDER" in str(exc.value)


def test_rejects_other_embedding_provider(monkeypatch):
    _clear_env(monkeypatch)
    with pytest.raises(ConfigError):
        load_settings(_env_file=None, EMBEDDING_PROVIDER="openai", **BASE)


def test_fake_llm_only_in_test_env(monkeypatch):
    _clear_env(monkeypatch)
    with pytest.raises(ConfigError):
        load_settings(_env_file=None, APP_ENV="development", LLM_USE_FAKE=True, **BASE)
    s = load_settings(_env_file=None, APP_ENV="test", LLM_USE_FAKE=True, **BASE)
    assert s.llm_configured


def test_secrets_never_in_repr(monkeypatch):
    _clear_env(monkeypatch)
    s = load_settings(_env_file=None, LLM_API_KEY="sk-supersecretvalue123", **BASE)
    assert "sk-supersecretvalue123" in s.secret_values()
