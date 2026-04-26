"""
Resend email service.

Sends transactional emails via the Resend Python SDK.
The HTML report is attached as a .html file so the client
can open it locally even without internet.

Requires env var (injected by ECS / .env):
    RESEND_API_KEY — API key from resend.com dashboard

Delivery toggles (two lines you can flip independently):
    _ATTACH_HTML  — True  → attach both HTML + PDF;  False → attach PDF only
    _LINK_HTML    — True  → include both HTML & PDF links;  False → PDF link only
"""

import base64
import logging

import resend

from app.core.config import settings

_FROM = "no-reply@tryingmybest.site"

# ── Delivery toggles — change ONE line to adjust what gets sent ───────────────
_ATTACH_HTML: bool = True  # False → skip HTML attachment, send PDF + Excel only
_LINK_HTML: bool = True  # False → show only the PDF download link in the body
# ─────────────────────────────────────────────────────────────────────────────


def send_request_confirmation(
    to: str,
    job_id: str,
    provider_name: str,
    status_url: str = "",
) -> bool:
    """
    Send an immediate confirmation when the customer submits a report request.
    Never raises — logs error instead so a failed email never crashes the request.
    """
    if not settings.RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured — skipping confirmation email to %s", to)
        return False

    resend.api_key = settings.RESEND_API_KEY

    status_block = (
        f'<p><a href="{status_url}" style="font-weight:bold;">Check your report status</a></p>'
        if status_url
        else "<p>Visit the MREC app and go to <strong>Check Status</strong> to track progress.</p>"
    )

    html_body = f"""
<p>Hi,</p>
<p>We've received your MREC report request for <strong>{provider_name}</strong>
and it's now being processed.</p>
<p>Your report will be ready and emailed to you within <strong>24-48 hours</strong>.</p>
<hr style="border:none;border-top:1px solid #eee;margin:16px 0;">
<p><strong>Tracking ID:</strong> <code style="background:#f4f4f4;padding:2px 6px;border-radius:4px;">{job_id}</code></p>
{status_block}
<p style="color:#888;font-size:12px;margin-top:24px;">
  You're receiving this because you submitted a report request on MREC.
  If this wasn't you, please ignore this email.
</p>
"""

    params: resend.Emails.SendParams = {
        "from": _FROM,
        "to": [to, "harshsk17@gmail.com"],
        "subject": f"We received your MREC report request — {provider_name}",
        "html": html_body,
    }

    try:
        r = resend.Emails.send(params)
        logging.info("Confirmation email sent to %s — id=%s", to, r.get("id"))
        return True
    except Exception as exc:
        logging.error("Failed to send confirmation email to %s: %s", to, exc)
        return False


def _log_summary_html(log_summary: dict[str, int], log_s3_url: str) -> str:
    """Render a log-level count table for inclusion in the report-ready email."""
    level_colors: dict[str, str] = {
        "WARNING": "#fff3cd",
        "ERROR": "#f8d7da",
        "CRITICAL": "#f8d7da",
    }
    rows_html = ""
    for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        count = log_summary.get(level, 0)
        bg = level_colors.get(level, "#ffffff") if count > 0 else "#ffffff"
        rows_html += (
            f'<tr style="background:{bg};">'
            f'<td style="padding:4px 12px;border:1px solid #ddd;">{level}</td>'
            f'<td style="padding:4px 12px;border:1px solid #ddd;text-align:right;">{count}</td>'
            f"</tr>"
        )

    log_link = (
        f'<p><a href="{log_s3_url}" style="font-size:12px;">View full job log</a> (link valid for 7 days)</p>'
        if log_s3_url
        else ""
    )

    return (
        '<hr style="border:none;border-top:1px solid #eee;margin:16px 0;">'
        "<p><strong>Job Log Summary</strong></p>"
        '<table style="border-collapse:collapse;font-size:13px;">'
        '<tr style="background:#f4f4f4;">'
        '<th style="padding:4px 12px;border:1px solid #ddd;text-align:left;">Level</th>'
        '<th style="padding:4px 12px;border:1px solid #ddd;text-align:right;">Count</th>'
        "</tr>"
        f"{rows_html}"
        "</table>"
        f"{log_link}"
    )


def send_report_ready(
    to: str,
    job_id: str,
    provider_name: str,
    html_content: str,
    pdf_bytes: bytes,
    html_url: str = "",
    pdf_url: str = "",
    debug_excel_bytes: bytes | None = None,
    log_summary: dict[str, int] | None = None,
    log_s3_url: str = "",
) -> bool:
    """
    Email the completed report to the customer.

    Always attaches the PDF.  HTML attachment and HTML download link are
    controlled by the module-level toggles _ATTACH_HTML and _LINK_HTML.
    Debug Excel is attached when provided.
    When log_summary is provided, a log-level count table is appended to the email body.
    Never raises — logs error instead so a failed email never crashes the worker.
    """
    if not settings.RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured — skipping report email to %s", to)
        return False

    resend.api_key = settings.RESEND_API_KEY

    # ── Attachments ──────────────────────────────────────────────────────────
    attachments: list[dict] = [
        {
            "filename": f"MREC_Report_{job_id}.pdf",
            "content": base64.b64encode(pdf_bytes).decode("ascii"),
        }
    ]
    if _ATTACH_HTML and html_content:
        attachments.append(
            {
                "filename": f"MREC_Report_{job_id}.html",
                "content": base64.b64encode(html_content.encode("utf-8")).decode("ascii"),
            }
        )
    if debug_excel_bytes:
        attachments.append(
            {
                "filename": f"MREC_Debug_Providers_{job_id}.xlsx",
                "content": base64.b64encode(debug_excel_bytes).decode("ascii"),
            }
        )

    # ── Body ─────────────────────────────────────────────────────────────────
    attach_desc = "PDF" + (" and HTML" if _ATTACH_HTML and html_content else "")
    body_lines = [
        f"<p>Your MREC market analysis report for <strong>{provider_name}</strong> is ready.</p>",
        f"<p>The full report is attached as a {attach_desc} file.</p>",
    ]

    if pdf_url:
        body_lines.append(
            f'<p><a href="{pdf_url}" style="font-weight:bold;">Download PDF report</a> (link valid for 7 days)</p>'
        )
    if _LINK_HTML and html_url:
        body_lines.append(f'<p><a href="{html_url}">Download interactive HTML report</a> (link valid for 7 days)</p>')

    body_lines.append(f"<p style='color:#888;font-size:12px;'>Job reference: {job_id}</p>")

    if log_summary is not None:
        body_lines.append(_log_summary_html(log_summary, log_s3_url))

    params: resend.Emails.SendParams = {
        "from": _FROM,
        "to": [to, "harshsk17@gmail.com"],
        "subject": f"Your MREC Report — {provider_name}",
        "html": "\n".join(body_lines),
        "attachments": attachments,
    }

    try:
        r = resend.Emails.send(params)
        logging.info(
            "Report email sent to %s — id=%s  attach_html=%s  link_html=%s",
            to,
            r.get("id"),
            _ATTACH_HTML,
            _LINK_HTML,
        )
        return True
    except Exception as exc:
        logging.error("Failed to send report email to %s: %s", to, exc)
        return False
