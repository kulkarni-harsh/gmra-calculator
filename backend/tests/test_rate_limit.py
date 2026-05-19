"""Tests for rate limit key extraction."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.rate_limit import client_id_key


@pytest.mark.unit
def test_client_id_key_uses_request_state_client():
    req = SimpleNamespace(
        state=SimpleNamespace(client="wix"),
        client=SimpleNamespace(host="1.2.3.4"),
    )
    assert client_id_key(req) == "wix:1.2.3.4"


@pytest.mark.unit
def test_client_id_key_falls_back_when_no_state():
    req = SimpleNamespace(
        state=SimpleNamespace(),
        client=SimpleNamespace(host="9.8.7.6"),
    )
    assert client_id_key(req) == "anonymous:9.8.7.6"


@pytest.mark.unit
def test_client_id_key_handles_missing_client_host():
    req = SimpleNamespace(
        state=SimpleNamespace(client="react"),
        client=None,
    )
    assert client_id_key(req) == "react:unknown"
