"""Unit tests for app.services.email — Resend SDK mocked."""

import base64
from unittest.mock import patch

# ── send_request_confirmation ─────────────────────────────────────────────────


def test_send_request_confirmation_returns_false_when_api_key_missing():
    with patch("app.services.email.settings") as s:
        s.RESEND_API_KEY = ""
        from app.services.email import send_request_confirmation

        ok = send_request_confirmation(to="x@y.com", job_id="J", provider_name="Dr A")
    assert ok is False


def test_send_request_confirmation_calls_resend_send():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_1"}) as send,
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_request_confirmation

        ok = send_request_confirmation(to="x@y.com", job_id="J", provider_name="Dr A")
    assert ok is True
    params = send.call_args.args[0]
    assert "x@y.com" in params["to"]
    assert "Dr A" in params["html"]


def test_send_request_confirmation_includes_job_id_in_html():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_2"}) as send,
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_request_confirmation

        send_request_confirmation(to="x@y.com", job_id="MERC-42", provider_name="Dr B")
    params = send.call_args.args[0]
    assert "MERC-42" in params["html"]


def test_send_request_confirmation_includes_status_url_when_provided():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_3"}) as send,
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_request_confirmation

        send_request_confirmation(
            to="x@y.com",
            job_id="J",
            provider_name="Dr C",
            status_url="https://example.com/status/J",
        )
    params = send.call_args.args[0]
    assert "https://example.com/status/J" in params["html"]


def test_send_request_confirmation_returns_false_when_resend_raises():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", side_effect=RuntimeError("503")),
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_request_confirmation

        ok = send_request_confirmation(to="x@y.com", job_id="J", provider_name="Dr A")
    assert ok is False


def test_send_request_confirmation_sets_subject_with_provider_name():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_4"}) as send,
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_request_confirmation

        send_request_confirmation(to="x@y.com", job_id="J", provider_name="Riverside Cardiology")
    params = send.call_args.args[0]
    assert "Riverside Cardiology" in params["subject"]


# ── send_report_ready ─────────────────────────────────────────────────────────


def test_send_report_ready_returns_false_when_api_key_missing():
    with patch("app.services.email.settings") as s:
        s.RESEND_API_KEY = ""
        from app.services.email import send_report_ready

        ok = send_report_ready(
            to="x@y.com",
            job_id="J",
            provider_name="Dr A",
            html_content="<html></html>",
            pdf_bytes=b"x",
        )
    assert ok is False


def test_send_report_ready_returns_true_on_success():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_5"}),
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_report_ready

        ok = send_report_ready(
            to="x@y.com",
            job_id="J",
            provider_name="Dr A",
            html_content="<html></html>",
            pdf_bytes=b"%PDF",
        )
    assert ok is True


def test_send_report_ready_attaches_pdf():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_6"}) as send,
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_report_ready

        pdf_data = b"%PDF-1.4"
        send_report_ready(
            to="x@y.com",
            job_id="MERC-7",
            provider_name="Dr A",
            html_content="<html></html>",
            pdf_bytes=pdf_data,
        )
    params = send.call_args.args[0]
    attachments = params["attachments"]
    filenames = [a["filename"] for a in attachments]
    assert any("MERC-7.pdf" in fn for fn in filenames)
    # Verify PDF content is base64-encoded correctly
    pdf_attach = next(a for a in attachments if ".pdf" in a["filename"])
    assert pdf_attach["content"] == base64.b64encode(pdf_data).decode("ascii")


def test_send_report_ready_attaches_html_when_attach_html_true():
    """When _ATTACH_HTML is True (default), an HTML file should be attached."""
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_7"}) as send,
        patch("app.services.email._ATTACH_HTML", True),
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_report_ready

        send_report_ready(
            to="x@y.com",
            job_id="MERC-8",
            provider_name="Dr A",
            html_content="<html>report</html>",
            pdf_bytes=b"%PDF",
        )
    params = send.call_args.args[0]
    filenames = [a["filename"] for a in params["attachments"]]
    assert any(".html" in fn for fn in filenames)


def test_send_report_ready_skips_html_attachment_when_attach_html_false():
    """When _ATTACH_HTML is False, no .html attachment should be present."""
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_8"}) as send,
        patch("app.services.email._ATTACH_HTML", False),
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_report_ready

        send_report_ready(
            to="x@y.com",
            job_id="MERC-9",
            provider_name="Dr A",
            html_content="<html>report</html>",
            pdf_bytes=b"%PDF",
        )
    params = send.call_args.args[0]
    filenames = [a["filename"] for a in params["attachments"]]
    assert not any(".html" in fn for fn in filenames)


def test_send_report_ready_attaches_debug_excel_when_provided():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_9"}) as send,
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_report_ready

        excel_data = b"PK\x03\x04"  # minimal xlsx header
        send_report_ready(
            to="x@y.com",
            job_id="MERC-10",
            provider_name="Dr A",
            html_content="<html></html>",
            pdf_bytes=b"%PDF",
            debug_excel_bytes=excel_data,
        )
    params = send.call_args.args[0]
    filenames = [a["filename"] for a in params["attachments"]]
    assert any(".xlsx" in fn for fn in filenames)
    xlsx_attach = next(a for a in params["attachments"] if ".xlsx" in a["filename"])
    assert xlsx_attach["content"] == base64.b64encode(excel_data).decode("ascii")


def test_send_report_ready_omits_debug_excel_when_not_provided():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_10"}) as send,
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_report_ready

        send_report_ready(
            to="x@y.com",
            job_id="MERC-11",
            provider_name="Dr A",
            html_content="<html></html>",
            pdf_bytes=b"%PDF",
        )
    params = send.call_args.args[0]
    filenames = [a["filename"] for a in params["attachments"]]
    assert not any(".xlsx" in fn for fn in filenames)


def test_send_report_ready_returns_false_when_resend_raises():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", side_effect=RuntimeError("network error")),
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_report_ready

        ok = send_report_ready(
            to="x@y.com",
            job_id="J",
            provider_name="Dr A",
            html_content="<html></html>",
            pdf_bytes=b"%PDF",
        )
    assert ok is False


def test_send_report_ready_sets_subject_with_provider_name():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_11"}) as send,
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_report_ready

        send_report_ready(
            to="x@y.com",
            job_id="J",
            provider_name="Pacific Neurology Group",
            html_content="<html></html>",
            pdf_bytes=b"%PDF",
        )
    params = send.call_args.args[0]
    assert "Pacific Neurology Group" in params["subject"]


def test_send_report_ready_includes_pdf_url_in_body_when_provided():
    with (
        patch("app.services.email.settings") as s,
        patch("app.services.email.resend.Emails.send", return_value={"id": "r_12"}) as send,
    ):
        s.RESEND_API_KEY = "re_test"
        from app.services.email import send_report_ready

        send_report_ready(
            to="x@y.com",
            job_id="J",
            provider_name="Dr A",
            html_content="<html></html>",
            pdf_bytes=b"%PDF",
            pdf_url="https://s3.example.com/report.pdf",
        )
    params = send.call_args.args[0]
    assert "https://s3.example.com/report.pdf" in params["html"]
