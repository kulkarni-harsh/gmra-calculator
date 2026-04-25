"""Unit tests for app.services.s3 — uploads + presigned URLs (boto3 mocked)."""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError


def test_upload_report_writes_html_with_correct_key_and_returns_url():
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://signed.example/r/job1.html"

    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_report

        url = upload_report("job1", "<h1>hello</h1>")

    mock_client.put_object.assert_called_once()
    kwargs = mock_client.put_object.call_args.kwargs
    assert kwargs["Key"].endswith("/job1.html")
    assert kwargs["ContentType"].startswith("text/html")
    assert kwargs["Body"] == b"<h1>hello</h1>"
    assert url == "https://signed.example/r/job1.html"


def test_upload_report_returns_empty_on_put_error():
    mock_client = MagicMock()
    mock_client.put_object.side_effect = ClientError({"Error": {"Code": "500", "Message": "fail"}}, "PutObject")
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_report

        url = upload_report("job1", "<html></html>")
    assert url == ""


def test_upload_report_returns_empty_on_presign_error():
    mock_client = MagicMock()
    mock_client.generate_presigned_url.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "fail"}}, "GeneratePresigned"
    )
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_report

        url = upload_report("job1", "<html></html>")
    assert url == ""


def test_upload_report_pdf_writes_and_returns_url():
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://signed.example/r/job1.pdf"
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_report_pdf

        url = upload_report_pdf("job1", b"%PDF-1.4 fake")
    kwargs = mock_client.put_object.call_args.kwargs
    assert kwargs["Key"].endswith("/job1.pdf")
    assert kwargs["ContentType"] == "application/pdf"
    assert kwargs["Body"] == b"%PDF-1.4 fake"
    assert url == "https://signed.example/r/job1.pdf"


def test_upload_report_pdf_returns_empty_on_put_error():
    mock_client = MagicMock()
    mock_client.put_object.side_effect = ClientError({"Error": {"Code": "500", "Message": "fail"}}, "PutObject")
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_report_pdf

        assert upload_report_pdf("job1", b"x") == ""


def test_upload_debug_excel_writes_xlsx_content_type():
    mock_client = MagicMock()
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_debug_excel

        key = upload_debug_excel("job1", b"PK fake xlsx")
    kwargs = mock_client.put_object.call_args.kwargs
    assert kwargs["Key"] == "debug/job1_providers.xlsx"
    assert "spreadsheetml" in kwargs["ContentType"]
    assert key == "debug/job1_providers.xlsx"


def test_upload_debug_excel_returns_empty_on_error():
    mock_client = MagicMock()
    mock_client.put_object.side_effect = ClientError({"Error": {"Code": "500", "Message": "fail"}}, "PutObject")
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_debug_excel

        assert upload_debug_excel("job1", b"x") == ""
