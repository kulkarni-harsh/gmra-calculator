# backend/tests/test_ecs_worker.py
from unittest.mock import MagicMock, patch


def _make_settings(cluster="arn:aws:ecs:us-east-1:123:cluster/c",
                   task_def="arn:aws:ecs:us-east-1:123:task-definition/app-worker:3",
                   subnets="subnet-a,subnet-b",
                   sg="sg-x"):
    m = MagicMock()
    m.ECS_CLUSTER_ARN = cluster
    m.WORKER_TASK_DEF_ARN = task_def
    m.WORKER_SUBNETS = subnets
    m.WORKER_SECURITY_GROUP = sg
    return m


def test_no_op_when_cluster_arn_empty():
    mock_settings = MagicMock()
    mock_settings.ECS_CLUSTER_ARN = ""
    with patch("app.services.ecs_worker.settings", mock_settings), \
         patch("app.services.ecs_worker.boto3") as mock_boto3:
        from app.services.ecs_worker import ensure_worker_running
        ensure_worker_running()
    mock_boto3.client.assert_not_called()


def test_runs_task_when_no_active_tasks():
    mock_settings = _make_settings()
    ecs_client = MagicMock()
    ecs_client.list_tasks.return_value = {"taskArns": []}

    import app.services.ecs_worker as m
    with patch.object(m, "settings", mock_settings), \
         patch.object(m, "_get_ecs", return_value=ecs_client):
        m.ensure_worker_running()

    ecs_client.run_task.assert_called_once()
    call_kwargs = ecs_client.run_task.call_args[1]
    assert call_kwargs["launchType"] == "FARGATE"
    assert call_kwargs["count"] == 1


def test_skips_run_task_when_worker_already_running():
    mock_settings = _make_settings()
    ecs_client = MagicMock()
    task_arn = "arn:aws:ecs:us-east-1:123:task/abc"
    ecs_client.list_tasks.return_value = {"taskArns": [task_arn]}
    ecs_client.describe_tasks.return_value = {
        "tasks": [{"taskArn": task_arn, "lastStatus": "RUNNING"}]
    }

    import app.services.ecs_worker as m
    with patch.object(m, "settings", mock_settings), \
         patch.object(m, "_get_ecs", return_value=ecs_client):
        m.ensure_worker_running()

    ecs_client.run_task.assert_not_called()


def test_runs_task_when_only_deactivating_task_exists():
    mock_settings = _make_settings()
    ecs_client = MagicMock()
    task_arn = "arn:aws:ecs:us-east-1:123:task/xyz"
    ecs_client.list_tasks.return_value = {"taskArns": [task_arn]}
    ecs_client.describe_tasks.return_value = {
        "tasks": [{"taskArn": task_arn, "lastStatus": "DEACTIVATING"}]
    }

    import app.services.ecs_worker as m
    with patch.object(m, "settings", mock_settings), \
         patch.object(m, "_get_ecs", return_value=ecs_client):
        m.ensure_worker_running()

    ecs_client.run_task.assert_called_once()


def test_swallows_ecs_api_errors():
    mock_settings = _make_settings()
    ecs_client = MagicMock()
    ecs_client.list_tasks.side_effect = Exception("network error")

    import app.services.ecs_worker as m
    with patch.object(m, "settings", mock_settings), \
         patch.object(m, "_get_ecs", return_value=ecs_client):
        # must NOT raise
        m.ensure_worker_running()
