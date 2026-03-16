"""
SQS worker — runs as a separate ECS service (same Docker image, different CMD).

Lifecycle:
  1. Load all lookup data from disk (once at startup)
  2. Long-poll SQS in a loop
  3. For each message: mark job running → generate report → store in DynamoDB
                       → email report to customer → mark done
  4. Delete SQS message (success or failure — DLQ catches repeated crashes)
"""

import asyncio
import json
import logging

from app.core.config import settings
from app.core.logging import configure_logging
from app.schemas.provider_request import ProviderRequest
from app.services.email import send_report_ready
from app.services.job_store import get_job, update_job
from app.services.queue import delete_message, receive_jobs
from app.services.report_generator import ReportState, load_state


async def process_job(job_id: str, state: ReportState) -> None:
    from app.services.report_generator import run_report

    job = get_job(job_id)
    if not job:
        logging.error("Job %s not found in DynamoDB — skipping", job_id)
        return

    update_job(job_id, status="running")
    logging.info("Job %s: status → running", job_id)

    try:
        payload = ProviderRequest.model_validate_json(job["payload"])
        html = await run_report(payload, state)

        # Store HTML in DynamoDB (~95 KB, well within the 400 KB item limit)
        update_job(job_id, status="done", result_html=html)
        logging.info("Job %s: status → done", job_id)

        # Email the report if the customer provided an address
        if payload.customer_email:
            send_report_ready(
                to=payload.customer_email,
                job_id=job_id,
                provider_name=payload.client_provider.name,
                html_report=html,
            )

    except Exception as exc:
        logging.error("Job %s: status → failed  error=%s", job_id, exc, exc_info=True)
        update_job(job_id, status="failed", error=str(exc))


async def main() -> None:
    configure_logging()
    logging.info("Worker starting — loading lookup data...")
    state = load_state()
    logging.info("Worker ready — polling SQS at %s", settings.SQS_QUEUE_URL)

    while True:
        messages = receive_jobs(max_messages=1, wait_seconds=20)
        for msg in messages:
            body = json.loads(msg["Body"])
            job_id = body.get("job_id", "<unknown>")
            logging.info("Received job %s from SQS", job_id)
            try:
                await process_job(job_id, state)
            finally:
                delete_message(msg["ReceiptHandle"])


if __name__ == "__main__":
    asyncio.run(main())
