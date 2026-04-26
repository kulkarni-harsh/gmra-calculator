"""Tests for Settings configuration."""
import pytest
from app.core.config import Settings


def test_ecs_settings_default_to_empty():
    """ECS environment variables default to empty string."""
    s = Settings(
        PROJECT_NAME="test",
        VERSION="0",
        API_PREFIX="/api",
        CENSUS_API_KEY="x",
        MAPBOX_API_KEY="x",
        ALPHASOPHIA_API_KEY="x",
        GOOGLE_API_KEY="x",
    )
    assert s.ECS_CLUSTER_ARN == ""
    assert s.WORKER_TASK_DEF_ARN == ""
    assert s.WORKER_SUBNETS == ""
    assert s.WORKER_SECURITY_GROUP == ""


def test_ecs_settings_read_from_env():
    """ECS environment variables can be set from constructor."""
    s = Settings(
        PROJECT_NAME="test",
        VERSION="0",
        API_PREFIX="/api",
        CENSUS_API_KEY="x",
        MAPBOX_API_KEY="x",
        ALPHASOPHIA_API_KEY="x",
        GOOGLE_API_KEY="x",
        ECS_CLUSTER_ARN="arn:aws:ecs:us-east-1:123:cluster/test",
        WORKER_TASK_DEF_ARN="arn:aws:ecs:us-east-1:123:task-definition/test-worker:5",
        WORKER_SUBNETS="subnet-aaa,subnet-bbb",
        WORKER_SECURITY_GROUP="sg-ccc",
    )
    assert s.ECS_CLUSTER_ARN == "arn:aws:ecs:us-east-1:123:cluster/test"
    assert s.WORKER_TASK_DEF_ARN == "arn:aws:ecs:us-east-1:123:task-definition/test-worker:5"
    assert s.WORKER_SUBNETS == "subnet-aaa,subnet-bbb"
    assert s.WORKER_SECURITY_GROUP == "sg-ccc"
