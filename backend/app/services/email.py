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
        "to": [to, "harshsk17@gmail.com"],
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
    html_content: str,
    pdf_bytes: bytes,
    html_url: str = "",
    pdf_url: str = "",
    debug_excel_bytes: bytes | None = None,
) -> bool:
    """
    Email the completed report to the customer.

    Always attaches the PDF.  HTML attachment and HTML download link are
    controlled by the module-level toggles _ATTACH_HTML and _LINK_HTML.
    Debug Excel is attached when provided.
    Never raises — logs error instead so a failed email never crashes the worker.
    """
    if not settings.RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured — skipping report email to %s", to)
        return False

    resend.api_key = settings.RESEND_API_KEY

    # ── Attachments ──────────────────────────────────────────────────────────
    attachments: list[dict] = [
        {
            "filename": f"MERC_Report_{job_id}.pdf",
            "content": base64.b64encode(pdf_bytes).decode("ascii"),
        }
    ]
    if _ATTACH_HTML and html_content:
        attachments.append(
            {
                "filename": f"MERC_Report_{job_id}.html",
                "content": base64.b64encode(html_content.encode("utf-8")).decode("ascii"),
            }
        )
    if debug_excel_bytes:
        attachments.append(
            {
                "filename": f"MERC_Debug_Providers_{job_id}.xlsx",
                "content": base64.b64encode(debug_excel_bytes).decode("ascii"),
            }
        )

    # ── Body ─────────────────────────────────────────────────────────────────
    attach_desc = "PDF" + (" and HTML" if _ATTACH_HTML and html_content else "")
    body_lines = [
        f"<p>Your MERC market analysis report for <strong>{provider_name}</strong> is ready.</p>",
        f"<p>The full report is attached as a {attach_desc} file.</p>",
    ]

    if pdf_url:
        body_lines.append(
            f'<p><a href="{pdf_url}" style="font-weight:bold;">Download PDF report</a> (link valid for 7 days)</p>'
        )
    if _LINK_HTML and html_url:
        body_lines.append(f'<p><a href="{html_url}">Download interactive HTML report</a> (link valid for 7 days)</p>')

    body_lines.append(f"<p style='color:#888;font-size:12px;'>Job reference: {job_id}</p>")

    params: resend.Emails.SendParams = {
        "from": _FROM,
        "to": [to, "harshsk17@gmail.com"],
        "subject": f"Your MERC Report — {provider_name}",
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
