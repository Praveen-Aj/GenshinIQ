"""Tests for configuration parsing."""

from pathlib import Path

from backend.config import Settings
from backend.services.cache_service import ShowcaseCacheService


def test_debug_accepts_release_alias(monkeypatch):
    monkeypatch.setenv("DEBUG", "release")

    settings = Settings()

    assert settings.DEBUG is False


def test_debug_accepts_true_alias(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")

    settings = Settings()

    assert settings.DEBUG is True


def test_showcase_cache_defaults_to_runtime_directory():
    cache = ShowcaseCacheService()

    assert cache.cache_dir == Path("data/runtime/showcases")
