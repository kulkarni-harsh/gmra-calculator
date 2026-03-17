"""DynamoDB CRUD for report generation jobs."""

import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


def _table():
    return boto3.resource("dynamodb", endpoint_url=settings.AWS_ENDPOINT_URL or None).Table(settings.DYNAMODB_TABLE_NAME)


class JobAlreadyExistsError(Exception):
    """Raised when a job_id already exists — prevents payment replay attacks."""


def create_job(
    job_id: str,
    payload_json: str,
    specialty_name: str,
    provider_name: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    try:
        _table().put_item(
            Item={
                "job_id": job_id,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
                "specialty_name": specialty_name,
                "provider_name": provider_name,
                "payload": payload_json,
                # "ttl": int(time.time()) + 7 * 24 * 3600,  # auto-delete after 7 days
            },
            ConditionExpression="attribute_not_exists(job_id)",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise JobAlreadyExistsError(job_id) from exc
        raise


def create_job_awaiting_payment(
    job_id: str,
    payload_json: str,
    specialty_name: str,
    provider_name: str,
) -> None:
    """Pre-create a job record at PaymentIntent creation time with status 'awaiting_payment'."""
    now = datetime.now(timezone.utc).isoformat()
    try:
        _table().put_item(
            Item={
                "job_id": job_id,
                "status": "awaiting_payment",
                "created_at": now,
                "updated_at": now,
                "specialty_name": specialty_name,
                "provider_name": provider_name,
                "payload": payload_json,
                "ttl": int(time.time()) + 7 * 24 * 3600,
            },
            ConditionExpression="attribute_not_exists(job_id)",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise JobAlreadyExistsError(job_id) from exc
        raise


def claim_job_for_generation(job_id: str) -> str:
    """
    Atomically transition a job from 'awaiting_payment' → 'pending'.
    Returns the stored payload JSON so the caller can enqueue the job.
    Raises JobAlreadyExistsError if the job was already claimed
    (webhook beat the browser, or a duplicate /generate call).
    """
    now = datetime.now(timezone.utc).isoformat()
    try:
        resp = _table().update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :pending, #updated_at = :now",
            ConditionExpression="#status = :awaiting",
            ExpressionAttributeNames={"#status": "status", "#updated_at": "updated_at"},
            ExpressionAttributeValues={
                ":pending": "pending",
                ":awaiting": "awaiting_payment",
                ":now": now,
            },
            ReturnValues="ALL_NEW",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise JobAlreadyExistsError(job_id) from exc
        raise
    return str(resp["Attributes"]["payload"])


def get_job(job_id: str) -> dict | None:
    resp = _table().get_item(Key={"job_id": job_id})
    return resp.get("Item")


def update_job(job_id: str, **fields) -> None:
    """Update arbitrary fields on a job record. Handles DynamoDB reserved words."""
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    set_parts: list[str] = []
    expr_names: dict[str, str] = {}
    expr_values: dict[str, object] = {}

    for k, v in fields.items():
        set_parts.append(f"#{k} = :{k}")
        expr_names[f"#{k}"] = k
        expr_values[f":{k}"] = v

    _table().update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET " + ", ".join(set_parts),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
