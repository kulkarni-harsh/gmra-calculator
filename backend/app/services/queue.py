"""SQS send / receive / delete helpers."""

import json

import boto3

from app.core.config import settings


def send_job(job_id: str) -> None:
    sqs = boto3.client("sqs")
    sqs.send_message(
        QueueUrl=settings.SQS_QUEUE_URL,
        MessageBody=json.dumps({"job_id": job_id}),
    )


def receive_jobs(max_messages: int = 1, wait_seconds: int = 20) -> list[dict]:
    """Long-poll the queue. Blocks up to wait_seconds if the queue is empty."""
    sqs = boto3.client("sqs")
    resp = sqs.receive_message(
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
    sqs = boto3.client("sqs")
    sqs.delete_message(QueueUrl=settings.SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
