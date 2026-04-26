"""SQS send / receive / delete helpers."""

import json

import boto3

from app.core.config import settings


def _sqs():
    return boto3.client("sqs", endpoint_url=settings.AWS_ENDPOINT_URL or None)


def send_job(job_id: str) -> None:
    _sqs().send_message(
        QueueUrl=settings.SQS_QUEUE_URL,
        MessageBody=json.dumps({"job_id": job_id}),
    )
    # Import here to avoid circular imports (ecs_worker → config, queue → config)
    from app.services.ecs_worker import ensure_worker_running
    ensure_worker_running()


def receive_jobs(max_messages: int = 1, wait_seconds: int = 20) -> list[dict]:
    """Long-poll the queue. Blocks up to wait_seconds if the queue is empty."""
    resp = _sqs().receive_message(
        QueueUrl=settings.SQS_QUEUE_URL,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=wait_seconds,
        # Keep message invisible for 15 min — longer than the worst-case report time.
        # If the worker dies, the message reappears after this window.
        VisibilityTimeout=900,
    )
    return resp.get("Messages", [])


def delete_message(receipt_handle: str) -> None:
    """Remove a message after successful processing."""
    _sqs().delete_message(QueueUrl=settings.SQS_QUEUE_URL, ReceiptHandle=receipt_handle)


def get_queue_depth() -> int:
    """Return the approximate number of messages visible in the queue."""
    resp = _sqs().get_queue_attributes(
        QueueUrl=settings.SQS_QUEUE_URL,
        AttributeNames=["ApproximateNumberOfMessages"],
    )
    return int(resp["Attributes"]["ApproximateNumberOfMessages"])
