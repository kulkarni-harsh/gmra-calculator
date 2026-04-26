"""
SQS worker — runs as a permanent ECS service (same Docker image, different CMD).

Lifecycle:
  1. Load all lookup data from disk (once at startup)
  2. Long-poll SQS in a loop indefinitely
  3. For each message: mark job running → generate report → upload to S3
                       → store in DynamoDB → email report to customer → mark done
  4. Delete SQS message (success only — visibility timeout expiry retries on failure)
"""

import asyncio
import json
import logging

from app.core.config import settings
from app.core.logging import JobLogHandler, configure_logging
from app.schemas.report_requests import T3ReportRequest
from app.services.email import send_report_ready
from app.services.job_store import get_job, update_job
from app.services.queue import delete_message, receive_jobs
from app.services.report_generator import ReportState, load_state


async def process_job(job_id: str, state: ReportState) -> None:
    from app.schemas.provider_request import ProviderRequest
    from app.schemas.report_requests import T1ReportRequest, T2ReportRequest
    from app.services._report_generator_a1_archived import run_report
    from app.services.pdf import html_to_pdf
    from app.services.report_generator import run_html_report
    from app.services.s3 import upload_job_log, upload_report, upload_report_pdf

    job = get_job(job_id)
    if not job:
        logging.error("Job %s not found in DynamoDB — skipping", job_id)
        return

    update_job(job_id, status="running")
    logging.info("Job %s: status → running", job_id)

    log_handler = JobLogHandler()
    logging.getLogger().addHandler(log_handler)

    try:
        raw = json.loads(job["payload"])
        report_type = raw.get("report_type", "a1")

        if report_type == "t3":
            t3_payload = T3ReportRequest.model_validate(raw)
            html, debug_excel_bytes = await run_html_report(
                t3_payload, state, job_id=job_id, custom_cpt_codes=t3_payload.cpt_codes
            )
        elif report_type == "t2":
            t2_payload = T2ReportRequest.model_validate(raw)
            html, debug_excel_bytes = await run_html_report(
                t2_payload, state, job_id=job_id, custom_cpt_codes=t2_payload.cpt_codes
            )
        elif report_type == "t1":
            t1_payload = T1ReportRequest.model_validate(raw)
            html, debug_excel_bytes = await run_html_report(t1_payload, state, job_id=job_id)
        else:
            a1_payload = ProviderRequest.model_validate(raw)
            html, debug_excel_bytes = await run_report(a1_payload, state, job_id=job_id)

        html_url = upload_report(job_id, html)
        pdf_bytes = await html_to_pdf(html)
        pdf_url = upload_report_pdf(job_id, pdf_bytes)

        update_job(
            job_id,
            status="done",
            report_s3_url=html_url,
            report_pdf_s3_url=pdf_url,
        )
        logging.info(
            "Job %s: status → done  html_url=%s  pdf_url=%s", job_id, html_url or "<none>", pdf_url or "<none>"
        )

        # Snapshot log before email so the summary is included in the email.
        log_summary = log_handler.summary
        log_s3_url = upload_job_log(job_id, log_handler.get_text())
        update_job(job_id, log_s3_url=log_s3_url, log_counts=log_summary)

        # Build email context from whichever payload branch was taken — avoids unbound variable refs.
        if report_type == "t3":
            email_to = str(t3_payload.customer_email)
            provider_label = f"{t3_payload.address_line_1}, {t3_payload.city}"
        elif report_type == "t2":
            email_to = str(t2_payload.customer_email)
            provider_label = f"{t2_payload.address_line_1}, {t2_payload.city}"
        elif report_type == "t1":
            email_to = str(t1_payload.customer_email)
            provider_label = f"{t1_payload.address_line_1}, {t1_payload.city}"
        else:
            email_to = str(a1_payload.customer_email)
            provider_label = str(a1_payload.client_provider.name)

        if email_to:
            send_report_ready(
                to=email_to,
                job_id=job_id,
                provider_name=provider_label,
                html_content=html,
                pdf_bytes=pdf_bytes,
                html_url=html_url or "",
                pdf_url=pdf_url or "",
                debug_excel_bytes=debug_excel_bytes,
                log_summary=log_summary,
                log_s3_url=log_s3_url,
            )

    except Exception as exc:
        logging.error("Job %s: status → failed  error=%s", job_id, exc, exc_info=True)
        log_summary = log_handler.summary
        log_s3_url = upload_job_log(job_id, log_handler.get_text())
        update_job(job_id, status="failed", error=str(exc), log_s3_url=log_s3_url, log_counts=log_summary)
        raise

    finally:
        logging.getLogger().removeHandler(log_handler)


async def main_loop(state: ReportState) -> None:
    """Poll SQS and process jobs indefinitely."""
    while True:
        messages = receive_jobs(max_messages=1, wait_seconds=20)

        if not messages:
            continue

        msg = messages[0]
        body = json.loads(msg["Body"])
        job_id = body.get("job_id", "<unknown>")
        logging.info("Received job %s from SQS", job_id)
        try:
            await process_job(job_id, state)
            delete_message(msg["ReceiptHandle"])
        except Exception as exc:  # intentionally broad — SQS retry handles failures
            logging.error(
                "Job %s: leaving message in queue — SQS will retry then route to DLQ: %s",
                job_id,
                exc,
            )


async def main() -> None:
    configure_logging()
    logging.info("Worker starting — loading lookup data...")
    state = load_state()
    logging.info("Worker ready — polling SQS at %s", settings.SQS_QUEUE_URL)
    await main_loop(state)
    logging.info("Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
