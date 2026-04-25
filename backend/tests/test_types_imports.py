def test_types_google_maps_no_unused_logging_import():
    """ruff F401 — logging was imported and never used."""
    import inspect

    from app.types import google_maps
    src = inspect.getsource(google_maps)
    assert "import logging" not in src, "remove unused logging import"
