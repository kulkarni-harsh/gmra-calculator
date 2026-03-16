"""
S3 service — stores HTML reports and returns pre-signed download URLs.

In production the bucket must exist before deployment.
For local dev the bucket is created by the LocalStack init script.
"""

import logging

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


def _client():
    return boto3.client("s3", endpoint_url=settings.AWS_ENDPOINT_URL or None)


def upload_report(job_id: str, html: str) -> str:
    """
    Upload an HTML report to S3 and return a pre-signed URL valid for
    settings.S3_PRESIGN_EXPIRY_SECONDS seconds.

    Key pattern: {prefix}/{job_id}.html
    Never raises — logs the error and returns "" on failure.
    """
    key = f"{settings.S3_REPORTS_PREFIX}/{job_id}.html"
    client = _client()

    try:
        client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=html.encode("utf-8"),
            ContentType="text/html; charset=utf-8",
        )
    except ClientError as exc:
        logging.error("S3 upload failed for job %s: %s", job_id, exc)
        return ""

    try:
        url: str = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
            ExpiresIn=settings.S3_PRESIGN_EXPIRY_SECONDS,
        )
        logging.info("S3 report uploaded for job %s — URL expires in %ds", job_id, settings.S3_PRESIGN_EXPIRY_SECONDS)
        return url
    except ClientError as exc:
        logging.error("Pre-sign failed for job %s: %s", job_id, exc)
        return ""


def upload_report_pdf(job_id: str, pdf_bytes: bytes) -> str:
    """
    Upload a PDF report to S3 and return a pre-signed URL valid for
    settings.S3_PRESIGN_EXPIRY_SECONDS seconds.

    Key pattern: {prefix}/{job_id}.pdf
    Never raises — logs the error and returns "" on failure.
    """
    key = f"{settings.S3_REPORTS_PREFIX}/{job_id}.pdf"
    client = _client()

    try:
        client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
    except ClientError as exc:
        logging.error("S3 PDF upload failed for job %s: %s", job_id, exc)
        return ""

    try:
        url: str = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
            ExpiresIn=settings.S3_PRESIGN_EXPIRY_SECONDS,
        )
        logging.info("S3 PDF uploaded for job %s — URL expires in %ds", job_id, settings.S3_PRESIGN_EXPIRY_SECONDS)
        return url
    except ClientError as exc:
        logging.error("PDF pre-sign failed for job %s: %s", job_id, exc)
        return ""
