"""Integration tests for /api/jobs/status/{job_id}."""

from unittest.mock import patch


def test_job_status_returns_404_when_missing(client):
    with patch("app.api.endpoints.jobs.get_job", return_value=None):
        r = client.get("/api/jobs/status/MERC-missing")
    assert r.status_code == 404


def test_job_status_returns_pending_state(client):
    with patch(
        "app.api.endpoints.jobs.get_job",
        return_value={
            "job_id": "MERC-1",
            "status": "pending",
            "created_at": "2026-04-25T00:00:00Z",
            "updated_at": "2026-04-25T00:00:01Z",
            "specialty_name": "Family Medicine",
            "provider_name": "Dr A",
        },
    ):
        r = client.get("/api/jobs/status/MERC-1")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"
    assert body["specialty_name"] == "Family Medicine"
    assert body["provider_name"] == "Dr A"


def test_job_status_returns_pdf_url_when_done(client):
    with patch(
        "app.api.endpoints.jobs.get_job",
        return_value={
            "job_id": "MERC-2",
            "status": "done",
            "created_at": "2026-04-25T00:00:00Z",
            "updated_at": "2026-04-25T00:01:00Z",
            "report_pdf_s3_url": "https://signed.example/report.pdf",
        },
    ):
        r = client.get("/api/jobs/status/MERC-2")
    assert r.status_code == 200
    assert r.json()["report_pdf_s3_url"] == "https://signed.example/report.pdf"


def test_job_status_returns_error_when_failed(client):
    with patch(
        "app.api.endpoints.jobs.get_job",
        return_value={
            "job_id": "MERC-3",
            "status": "failed",
            "created_at": "2026-04-25T00:00:00Z",
            "updated_at": "2026-04-25T00:00:30Z",
            "error": "AlphaSophia 504",
        },
    ):
        r = client.get("/api/jobs/status/MERC-3")
    assert r.status_code == 200
    assert r.json()["error"] == "AlphaSophia 504"
