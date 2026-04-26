"""Unit tests for app.services.queue — SQS wrappers (boto3 mocked)."""

import json
from unittest.mock import MagicMock, patch


def _make_sqs_mock():
    """Return a fresh MagicMock that stands in for the boto3 SQS client."""
    return MagicMock()


# ---------------------------------------------------------------------------
# send_job
# ---------------------------------------------------------------------------


def test_send_job_serializes_job_id_to_message_body():
    """send_job encodes job_id as JSON in MessageBody."""
    mock_client = _make_sqs_mock()
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import send_job

        send_job("MERC-abc")

    mock_client.send_message.assert_called_once()
    kwargs = mock_client.send_message.call_args.kwargs
    body = json.loads(kwargs["MessageBody"])
    assert body == {"job_id": "MERC-abc"}


def test_send_job_uses_queue_url_from_settings():
    """send_job passes the QueueUrl from settings."""
    mock_client = _make_sqs_mock()
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import send_job

        send_job("MERC-xyz")

    kwargs = mock_client.send_message.call_args.kwargs
    assert "QueueUrl" in kwargs


# ---------------------------------------------------------------------------
# receive_jobs
# ---------------------------------------------------------------------------


def test_receive_jobs_returns_messages_list():
    """receive_jobs forwards max_messages and wait_seconds and returns Messages."""
    mock_client = _make_sqs_mock()
    mock_client.receive_message.return_value = {"Messages": [{"Body": '{"job_id":"MERC-1"}', "ReceiptHandle": "r1"}]}
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import receive_jobs

        msgs = receive_jobs(max_messages=2, wait_seconds=5)

    mock_client.receive_message.assert_called_once()
    kwargs = mock_client.receive_message.call_args.kwargs
    assert kwargs["MaxNumberOfMessages"] == 2
    assert kwargs["WaitTimeSeconds"] == 5
    assert len(msgs) == 1
    assert msgs[0]["ReceiptHandle"] == "r1"


def test_receive_jobs_returns_empty_list_when_no_messages():
    """receive_jobs returns [] when the SQS response has no Messages key."""
    mock_client = _make_sqs_mock()
    mock_client.receive_message.return_value = {}  # no Messages key
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import receive_jobs

        msgs = receive_jobs()

    assert msgs == []


def test_receive_jobs_default_params():
    """receive_jobs uses default max_messages=1 and wait_seconds=20."""
    mock_client = _make_sqs_mock()
    mock_client.receive_message.return_value = {}
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import receive_jobs

        receive_jobs()

    kwargs = mock_client.receive_message.call_args.kwargs
    assert kwargs["MaxNumberOfMessages"] == 1
    assert kwargs["WaitTimeSeconds"] == 20


def test_receive_jobs_sets_visibility_timeout():
    """receive_jobs always sets VisibilityTimeout to 900 seconds."""
    mock_client = _make_sqs_mock()
    mock_client.receive_message.return_value = {}
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import receive_jobs

        receive_jobs()

    kwargs = mock_client.receive_message.call_args.kwargs
    assert kwargs["VisibilityTimeout"] == 900


# ---------------------------------------------------------------------------
# delete_message
# ---------------------------------------------------------------------------


def test_delete_message_passes_receipt_handle():
    """delete_message forwards ReceiptHandle to boto3."""
    mock_client = _make_sqs_mock()
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import delete_message

        delete_message("receipt-xyz")

    mock_client.delete_message.assert_called_once()
    kwargs = mock_client.delete_message.call_args.kwargs
    assert kwargs["ReceiptHandle"] == "receipt-xyz"


def test_delete_message_uses_queue_url_from_settings():
    """delete_message passes QueueUrl from settings."""
    mock_client = _make_sqs_mock()
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import delete_message

        delete_message("some-receipt")

    kwargs = mock_client.delete_message.call_args.kwargs
    assert "QueueUrl" in kwargs


# ---------------------------------------------------------------------------
# ensure_worker_running wiring
# ---------------------------------------------------------------------------


def test_send_job_calls_ensure_worker_running():
    """send_job triggers ensure_worker_running after enqueuing."""
    mock_client = _make_sqs_mock()
    with patch("app.services.queue._sqs", return_value=mock_client), \
         patch("app.services.ecs_worker.ensure_worker_running") as mock_ensure:
        from app.services.queue import send_job
        send_job("MERC-123")
    mock_ensure.assert_called_once()


def test_send_job_calls_ensure_even_after_successful_send():
    """ensure_worker_running is called after a successful send_message."""
    mock_client = _make_sqs_mock()
    mock_client.send_message.return_value = {"MessageId": "abc"}
    with patch("app.services.queue._sqs", return_value=mock_client), \
         patch("app.services.ecs_worker.ensure_worker_running") as mock_ensure:
        from app.services.queue import send_job
        send_job("MERC-xyz")
    assert mock_client.send_message.called
    assert mock_ensure.called


def test_send_job_does_not_call_ensure_if_send_message_raises():
    """ensure_worker_running must not be called when the SQS send fails."""
    mock_client = _make_sqs_mock()
    mock_client.send_message.side_effect = Exception("SQS unavailable")
    with patch("app.services.queue._sqs", return_value=mock_client), \
         patch("app.services.ecs_worker.ensure_worker_running") as mock_ensure:
        import pytest
        from app.services.queue import send_job
        with pytest.raises(Exception, match="SQS unavailable"):
            send_job("MERC-fail")
    mock_ensure.assert_not_called()


# ---------------------------------------------------------------------------
# get_queue_depth
# ---------------------------------------------------------------------------


def test_get_queue_depth_returns_int():
    """get_queue_depth parses ApproximateNumberOfMessages as int."""
    mock_client = _make_sqs_mock()
    mock_client.get_queue_attributes.return_value = {
        "Attributes": {"ApproximateNumberOfMessages": "7"}
    }
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import get_queue_depth
        assert get_queue_depth() == 7


def test_get_queue_depth_returns_zero_on_empty_queue():
    """get_queue_depth returns 0 when queue is empty."""
    mock_client = _make_sqs_mock()
    mock_client.get_queue_attributes.return_value = {
        "Attributes": {"ApproximateNumberOfMessages": "0"}
    }
    with patch("app.services.queue._sqs", return_value=mock_client):
        from app.services.queue import get_queue_depth
        assert get_queue_depth() == 0
