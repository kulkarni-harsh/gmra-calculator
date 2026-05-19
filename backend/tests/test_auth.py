"""Tests for require_api_key dependency."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import auth as auth_mod
from app.core.auth import require_api_key


def _make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected", dependencies=[__import__("fastapi").Depends(require_api_key)])
    def protected() -> dict[str, str]:
        return {"ok": "true"}

    return app


@pytest.fixture
def patched_settings(monkeypatch):
    """Provide a controlled settings object to auth module."""

    class Stub:
        AUTH_ENFORCED = True
        API_KEY_WIX = "wix-secret-key"
        API_KEY_REACT = "react-secret-key"
        INTERNAL_ORIGINS = "https://merc.example.com,https://www.merc.example.com"

    monkeypatch.setattr(auth_mod, "settings", Stub())
    return Stub


@pytest.mark.unit
def test_valid_wix_key_passes(patched_settings):
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"X-API-Key": "wix-secret-key"})
    assert r.status_code == 200


@pytest.mark.unit
def test_valid_react_key_passes(patched_settings):
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"X-API-Key": "react-secret-key"})
    assert r.status_code == 200


@pytest.mark.unit
def test_invalid_key_rejected(patched_settings):
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


@pytest.mark.unit
def test_missing_key_no_origin_rejected(patched_settings):
    client = TestClient(_make_app())
    r = client.get("/protected")
    assert r.status_code == 401


@pytest.mark.unit
def test_internal_origin_bypass_allowed(patched_settings):
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"Origin": "https://merc.example.com"})
    assert r.status_code == 200


@pytest.mark.unit
def test_external_origin_without_key_rejected(patched_settings):
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"Origin": "https://evil.example.com"})
    assert r.status_code == 401


@pytest.mark.unit
def test_auth_disabled_lets_anything_through(monkeypatch):
    class Stub:
        AUTH_ENFORCED = False
        API_KEY_WIX = "x"
        API_KEY_REACT = "y"
        INTERNAL_ORIGINS = ""

    monkeypatch.setattr(auth_mod, "settings", Stub())
    client = TestClient(_make_app())
    r = client.get("/protected")
    assert r.status_code == 200
