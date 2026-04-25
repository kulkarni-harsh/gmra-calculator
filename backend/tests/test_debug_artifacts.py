import pytest


def test_enable_debug_artifacts_default_true():
    """ENABLE_DEBUG_ARTIFACTS must default to True."""
    from app.core.config import Settings
    s = Settings(
        PROJECT_NAME="test", VERSION="0", API_PREFIX="/api",
        CENSUS_API_KEY="x", MAPBOX_API_KEY="x",
        ALPHASOPHIA_API_KEY="x", GOOGLE_API_KEY="x",
    )
    assert s.ENABLE_DEBUG_ARTIFACTS is True


def test_enable_debug_artifacts_can_be_disabled():
    """ENABLE_DEBUG_ARTIFACTS can be explicitly set to False."""
    from app.core.config import Settings
    s = Settings(
        PROJECT_NAME="test", VERSION="0", API_PREFIX="/api",
        CENSUS_API_KEY="x", MAPBOX_API_KEY="x",
        ALPHASOPHIA_API_KEY="x", GOOGLE_API_KEY="x",
        ENABLE_DEBUG_ARTIFACTS=False,
    )
    assert s.ENABLE_DEBUG_ARTIFACTS is False


def test_upload_debug_json_puts_correct_key():
    """upload_debug_json must write to debug/{job_id}/{stage}.json."""
    from unittest.mock import MagicMock, patch

    mock_client = MagicMock()
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_debug_json
        result = upload_debug_json("job123", "01_providers_raw", [{"npi": "1"}])

    mock_client.put_object.assert_called_once()
    call_kwargs = mock_client.put_object.call_args.kwargs
    assert call_kwargs["Key"] == "debug/job123/01_providers_raw.json"
    assert call_kwargs["ContentType"] == "application/json"
    assert result == "debug/job123/01_providers_raw.json"


def test_upload_debug_json_returns_empty_string_on_error():
    """upload_debug_json must never raise — return '' on failure."""
    from unittest.mock import MagicMock, patch
    from botocore.exceptions import ClientError

    mock_client = MagicMock()
    mock_client.put_object.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "fail"}}, "PutObject"
    )
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_debug_json
        result = upload_debug_json("job123", "01_providers_raw", [])

    assert result == ""
