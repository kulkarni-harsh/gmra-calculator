from datetime import datetime


def test_health_returns_ok_status(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "timestamp" in payload


def test_health_timestamp_is_iso_utc(client):
    response = client.get("/api/health")
    ts = response.json()["timestamp"]
    parsed = datetime.fromisoformat(ts)
    assert parsed.utcoffset() is not None, "timestamp must include UTC offset"
    assert parsed.utcoffset().total_seconds() == 0, "timestamp must be UTC"


def test_health_module_uses_datetime_utc_alias():
    """Per ruff UP017, prefer `datetime.UTC` over `datetime.timezone.utc`."""
    import inspect

    from app.api.endpoints import health
    src = inspect.getsource(health)
    assert "timezone.utc" not in src, "use datetime.UTC alias"


def test_main_module_has_no_print_calls():
    """app/main.py must use logging, not print()."""
    import inspect

    from app import main
    src = inspect.getsource(main)
    assert "print(" not in src, "use logging.info(...) instead of print(...)"
