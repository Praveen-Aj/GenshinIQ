"""Automated tests for Phase 0 Foundation & Health endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import settings

client = TestClient(app)


def test_health_endpoint():
    """Verify that /api/health returns 200 and expected payload structure."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == settings.APP_NAME
    assert data["version"] == settings.APP_VERSION
    assert data["environment"] == settings.APP_ENV
    assert "timestamp" in data
    assert data["enka_api_base"] == settings.ENKA_API_BASE_URL


def test_frontend_static_serving():
    """Verify that frontend static index.html is served at root /."""
    response = client.get("/")
    assert response.status_code == 200
    assert "GenshinIQ" in response.text
    assert "text/html" in response.headers.get("content-type", "")


def test_settings_configuration():
    """Verify settings configuration loading."""
    assert settings.APP_NAME == "GenshinIQ"
    assert settings.PORT == 8000
    assert settings.ENKA_CACHE_TTL_SECONDS == 300
