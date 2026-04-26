"""Ensure exactly one worker ECS task is running when jobs are queued."""

import logging
from typing import Any

import boto3

from app.core.config import settings

_ACTIVE_STATUSES = frozenset({"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING"})


def _get_ecs() -> Any:
    return boto3.client("ecs")


def ensure_worker_running() -> None:
    """Start a worker Fargate task if none is currently active.

    Fire-and-forget: errors are logged but never re-raised so that the
    calling enqueue path is never broken by ECS API issues.
    The job is already safely in SQS; a subsequent request will retry.
    """
    if not settings.ECS_CLUSTER_ARN:
        return  # local dev — no ECS, skip

    try:
        ecs = _get_ecs()
        cluster = settings.ECS_CLUSTER_ARN

        # List tasks for the worker family that ECS considers "running"
        resp = ecs.list_tasks(
            cluster=cluster,
            family=settings.WORKER_TASK_DEF_ARN.split("/")[-1].split(":")[0],
            desiredStatus="RUNNING",
        )
        task_arns = resp.get("taskArns", [])

        if task_arns:
            # Describe to get lastStatus — filter out DEACTIVATING/STOPPING/STOPPED
            described = ecs.describe_tasks(cluster=cluster, tasks=task_arns)
            active = [
                t for t in described.get("tasks", [])
                if t.get("lastStatus") in _ACTIVE_STATUSES
            ]
            if active:
                logging.debug(
                    "ensure_worker_running: worker already active (%s), skipping RunTask",
                    active[0].get("lastStatus"),
                )
                return

        # No active worker — launch one
        subnets = [s.strip() for s in settings.WORKER_SUBNETS.split(",") if s.strip()]
        result = ecs.run_task(
            cluster=cluster,
            taskDefinition=settings.WORKER_TASK_DEF_ARN,
            launchType="FARGATE",
            count=1,
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": subnets,
                    "securityGroups": [settings.WORKER_SECURITY_GROUP],
                    "assignPublicIp": "ENABLED",
                }
            },
        )
        failures = result.get("failures", [])
        if failures:
            logging.error("ensure_worker_running: RunTask reported failures: %s", failures)
        else:
            logging.info(
                "ensure_worker_running: launched worker task %s",
                result["tasks"][0]["taskArn"],
            )

    except Exception:  # intentionally broad — fire-and-forget; job is safe in SQS
        logging.exception("ensure_worker_running: failed to launch worker — job remains in SQS")
