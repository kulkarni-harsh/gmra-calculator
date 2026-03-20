"""
SQS worker — runs as a separate ECS service (same Docker image, different CMD).

Lifecycle:
  1. Load all lookup data from disk (once at startup)
  2. Long-poll SQS in a loop
  3. For each message: mark job running → generate report → upload to S3
                       → store in DynamoDB → email report to customer → mark done
  4. Delete SQS message (success or failure — DLQ catches repeated crashes)
"""

import asyncio
import json
import logging

from app.core.config import settings
from app.core.logging import configure_logging
from app.services.email import send_report_ready
from app.services.job_store import get_job, update_job
from app.services.queue import delete_message, receive_jobs
from app.services.report_generator import ReportState, load_state


async def process_job(job_id: str, state: ReportState) -> None:
    from app.schemas.address_report_request import AddressReportRequest
    from app.schemas.provider_request import ProviderRequest
    from app.services.pdf import html_to_pdf
    from app.services.report_generator import run_report
    from app.services.s3 import upload_report, upload_report_pdf
    from app.services.t0_report_generator import run_t0_report

    job = get_job(job_id)
    if not job:
        logging.error("Job %s not found in DynamoDB — skipping", job_id)
        return

    update_job(job_id, status="running")
    logging.info("Job %s: status → running", job_id)

    try:
        raw = json.loads(job["payload"])
        report_type = raw.get("report_type", "t0")

        if report_type == "t0":
            t0_payload = AddressReportRequest.model_validate(raw)
            html, debug_excel_bytes = await run_t0_report(t0_payload, state, job_id=job_id)
        else:
            t1_payload = ProviderRequest.model_validate(raw)
            html, debug_excel_bytes = await run_report(t1_payload, state, job_id=job_id)

        html_url = upload_report(job_id, html)
        pdf_bytes = html_to_pdf(html)
        pdf_url = upload_report_pdf(job_id, pdf_bytes)

        update_job(
            job_id,
            status="done",
            result_html=html,
            report_s3_url=html_url,
            report_pdf_s3_url=pdf_url,
        )
        logging.info("Job %s: status → done  html_url=%s  pdf_url=%s", job_id, html_url or "<none>", pdf_url or "<none>")

        # Build email context from whichever payload branch was taken — avoids unbound variable refs.
        if report_type == "t0":
            email_to = str(t0_payload.customer_email)
            provider_label = f"{t0_payload.address_line_1}, {t0_payload.city}"
        else:
            email_to = str(t1_payload.customer_email)
            provider_label = str(t1_payload.client_provider.name)

        if email_to:
            send_report_ready(
                to=email_to,
                job_id=job_id,
                provider_name=provider_label,
                html_content=html,
                report_url=html_url,
                attachment_format="html",
                debug_excel_bytes=debug_excel_bytes,
            )

    except Exception as exc:
        logging.error("Job %s: status → failed  error=%s", job_id, exc, exc_info=True)
        update_job(job_id, status="failed", error=str(exc))
        raise


async def main() -> None:
    configure_logging()
    logging.info("Worker starting — loading lookup data...")
    state = load_state()
    logging.info("Worker ready — polling SQS at %s", settings.SQS_QUEUE_URL)

    while True:
        messages = receive_jobs(max_messages=1, wait_seconds=20)
        print("messages", messages)
        for msg in messages:
            body = json.loads(msg["Body"])
            job_id = body.get("job_id", "<unknown>")
            logging.info("Received job %s from SQS", job_id)
            try:
                await process_job(job_id, state)
                delete_message(msg["ReceiptHandle"])  # only on success
            except Exception as exc:
                logging.error(
                    "Job %s: leaving message in queue — SQS will retry then route to DLQ: %s",
                    job_id,
                    exc,
                )
                # Do NOT delete — visibility timeout expires, SQS retries up to
                # maxReceiveCount, then moves the message to the DLQ automatically.


if __name__ == "__main__":
    asyncio.run(main())
