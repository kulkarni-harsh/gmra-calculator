"""DynamoDB CRUD for report generation jobs."""

import time
from datetime import datetime, timezone

import boto3

from app.core.config import settings


def _table():
    return boto3.resource("dynamodb", endpoint_url=settings.AWS_ENDPOINT_URL or None).Table(settings.DYNAMODB_TABLE_NAME)


def create_job(
    job_id: str,
    payload_json: str,
    specialty_name: str,
    provider_name: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
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
        }
    )


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
