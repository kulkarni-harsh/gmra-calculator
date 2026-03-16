"""Convert HTML strings to PDF bytes using weasyprint."""

import logging

from weasyprint import HTML


def html_to_pdf(html: str) -> bytes:
    """
    Render an HTML string to PDF bytes.

    Never raises — logs the error and re-raises so the worker can mark the job failed.
    """
    log = logging.getLogger(__name__)
    try:
        pdf_bytes: bytes = HTML(string=html).write_pdf()
        log.info("PDF rendered — %d bytes", len(pdf_bytes))
        return pdf_bytes
    except Exception as exc:
        log.error("PDF conversion failed: %s", exc)
        raise
