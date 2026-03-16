"""
Resend email service.

Sends transactional emails via the Resend Python SDK.
The HTML report is attached as a .html file so the client
can open it locally even without internet.

Requires env var (injected by ECS / .env):
    RESEND_API_KEY — API key from resend.com dashboard
"""

import base64
import logging

import resend

from app.core.config import settings

_FROM = "no-reply@tryingmybest.site"


def send_request_confirmation(
    to: str,
    job_id: str,
    provider_name: str,
    status_url: str = "",
) -> bool:
    """
    Send an immediate confirmation when the customer submits a report request.
    Includes the tracking ID, a link to check status, and an ETA of 1 hour.
    Never raises — logs error instead so a failed email never crashes the request.
    """
    if not settings.RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured — skipping confirmation email to %s", to)
        return False

    resend.api_key = settings.RESEND_API_KEY

    status_block = (
        f'<p><a href="{status_url}" style="font-weight:bold;">Check your report status</a></p>'
        if status_url
        else "<p>Visit the MERC app and go to <strong>Check Status</strong> to track progress.</p>"
    )

    html_body = f"""
<p>Hi,</p>
<p>We've received your MERC report request for <strong>{provider_name}</strong>
and it's now being processed.</p>
<p>Your report will be ready and emailed to you within <strong>1 hour</strong>.</p>
<hr style="border:none;border-top:1px solid #eee;margin:16px 0;">
<p><strong>Tracking ID:</strong> <code style="background:#f4f4f4;padding:2px 6px;border-radius:4px;">{job_id}</code></p>
{status_block}
<p style="color:#888;font-size:12px;margin-top:24px;">
  You're receiving this because you submitted a report request on MERC.
  If this wasn't you, please ignore this email.
</p>
"""

    params: resend.Emails.SendParams = {
        "from": _FROM,
        "to": [to],
        "subject": f"We received your MERC report request — {provider_name}",
        "html": html_body,
    }

    try:
        r = resend.Emails.send(params)
        logging.info("Confirmation email sent to %s — id=%s", to, r.get("id"))
        return True
    except Exception as exc:
        logging.error("Failed to send confirmation email to %s: %s", to, exc)
        return False


def send_report_ready(
    to: str,
    job_id: str,
    provider_name: str,
    html_report: str,
    report_url: str = "",
) -> bool:
    """
    Email the completed report to the customer.

    - HTML report is attached as 'MERC_Report_{job_id}.html'
    - If report_url is provided, it is included as a download link in the body
    - Returns True on success, False on failure
    - Never raises — logs error instead so a failed email never crashes the worker
    """
    if not settings.RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured — skipping email to %s", to)
        return False

    resend.api_key = settings.RESEND_API_KEY

    body_paragraphs = [
        f"<p>Your MERC market analysis report for <strong>{provider_name}</strong> is ready.</p>",
        "<p>The full report is attached to this email as an HTML file. "
        "Open it in any browser to view your competitive analysis.</p>",
    ]
    if report_url:
        body_paragraphs.append(
            f'<p><a href="{report_url}" style="font-weight:bold;">Click here to download the report</a> '
            "(link valid for 7 days)</p>"
        )
    body_paragraphs.append(f"<p style='color:#888;font-size:12px;'>Job reference: {job_id}</p>")
    html_body = "\n".join(body_paragraphs)

    encoded_content = base64.b64encode(html_report.encode("utf-8")).decode("ascii")

    params: resend.Emails.SendParams = {
        "from": _FROM,
        "to": [to],
        "subject": f"Your MERC Report — {provider_name}",
        "html": html_body,
        "attachments": [
            {
                "filename": f"MERC_Report_{job_id}.html",
                "content": encoded_content,
            }
        ],
    }

    try:
        r = resend.Emails.send(params)
        logging.info("Resend email sent to %s — id=%s", to, r.get("id"))
        return True
    except Exception as exc:
        logging.error("Failed to send Resend email to %s: %s", to, exc)
        return False
