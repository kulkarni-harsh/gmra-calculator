"""Unit tests for app.services.job_store — DynamoDB CRUD with boto3 mocked."""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError


def _make_table(get_item_return=None, update_item_return=None) -> MagicMock:
    table = MagicMock()
    if get_item_return is not None:
        table.get_item.return_value = get_item_return
    if update_item_return is not None:
        table.update_item.return_value = update_item_return
    return table


def test_create_job_writes_pending_item():
    """create_job puts an item with status=pending and all required fields."""
    table = MagicMock()
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import create_job

        create_job("MREC-1", '{"k":"v"}', "Family Medicine", "Dr A")

    item = table.put_item.call_args.kwargs["Item"]
    assert item["job_id"] == "MREC-1"
    assert item["status"] == "pending"
    assert item["specialty_name"] == "Family Medicine"
    assert item["provider_name"] == "Dr A"
    assert item["payload"] == '{"k":"v"}'
    assert "created_at" in item and "updated_at" in item


def test_create_job_raises_job_already_exists_on_conditional_failure():
    """create_job raises JobAlreadyExistsError on ConditionalCheckFailedException."""
    table = MagicMock()
    table.put_item.side_effect = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "exists"}},
        "PutItem",
    )
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import JobAlreadyExistsError, create_job

        with pytest.raises(JobAlreadyExistsError):
            create_job("MREC-1", "{}", "x", "y")


def test_create_job_reraises_other_client_errors():
    """create_job re-raises ClientError codes other than ConditionalCheckFailedException."""
    table = MagicMock()
    table.put_item.side_effect = ClientError(
        {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "throttled"}},
        "PutItem",
    )
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import create_job

        with pytest.raises(ClientError):
            create_job("MREC-1", "{}", "x", "y")


def test_create_job_awaiting_payment_sets_correct_status():
    """create_job_awaiting_payment puts an item with status=awaiting_payment."""
    table = MagicMock()
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import create_job_awaiting_payment

        create_job_awaiting_payment("MREC-2", "{}", "FM", "Dr B")
    item = table.put_item.call_args.kwargs["Item"]
    assert item["status"] == "awaiting_payment"


def test_create_job_awaiting_payment_has_ttl():
    """create_job_awaiting_payment includes a TTL field for auto-expiry."""
    table = MagicMock()
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import create_job_awaiting_payment

        create_job_awaiting_payment("MREC-2", "{}", "FM", "Dr B")
    item = table.put_item.call_args.kwargs["Item"]
    assert "ttl" in item
    assert isinstance(item["ttl"], int)


def test_create_job_awaiting_payment_raises_job_already_exists_on_conditional_failure():
    """create_job_awaiting_payment raises JobAlreadyExistsError on duplicate job_id."""
    table = MagicMock()
    table.put_item.side_effect = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "exists"}},
        "PutItem",
    )
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import JobAlreadyExistsError, create_job_awaiting_payment

        with pytest.raises(JobAlreadyExistsError):
            create_job_awaiting_payment("MREC-2", "{}", "FM", "Dr B")


def test_claim_job_for_generation_returns_payload():
    """claim_job_for_generation returns the payload string from the updated item."""
    table = _make_table(update_item_return={"Attributes": {"payload": '{"k":"v"}'}})
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import claim_job_for_generation

        payload = claim_job_for_generation("MREC-3")
    assert payload == '{"k":"v"}'


def test_claim_job_for_generation_transitions_status():
    """claim_job_for_generation sets status=pending via UpdateExpression."""
    table = _make_table(update_item_return={"Attributes": {"payload": "{}"}})
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import claim_job_for_generation

        claim_job_for_generation("MREC-3")

    kwargs = table.update_item.call_args.kwargs
    expr_values = kwargs["ExpressionAttributeValues"]
    assert expr_values[":pending"] == "pending"
    assert expr_values[":awaiting"] == "awaiting_payment"


def test_claim_job_for_generation_raises_when_already_claimed():
    """claim_job_for_generation raises JobAlreadyExistsError if already transitioned."""
    table = MagicMock()
    table.update_item.side_effect = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "exists"}},
        "UpdateItem",
    )
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import JobAlreadyExistsError, claim_job_for_generation

        with pytest.raises(JobAlreadyExistsError):
            claim_job_for_generation("MREC-3")


def test_get_job_returns_item():
    """get_job returns the item dict when found."""
    table = _make_table(get_item_return={"Item": {"job_id": "MREC-4", "status": "done"}})
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import get_job

        out = get_job("MREC-4")
    assert out is not None and out["job_id"] == "MREC-4"


def test_get_job_returns_none_when_missing():
    """get_job returns None when the job_id is not in the table."""
    table = _make_table(get_item_return={})  # no Item key
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import get_job

        assert get_job("MREC-x") is None


def test_update_job_sets_arbitrary_fields():
    """update_job builds a SET expression covering the supplied fields."""
    table = MagicMock()
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import update_job

        update_job("MREC-5", status="done", report_s3_url="https://x/y.html")
    kwargs = table.update_item.call_args.kwargs
    expr = kwargs["UpdateExpression"]
    assert expr.startswith("SET ")


def test_update_job_includes_updated_at():
    """update_job always stamps updated_at regardless of caller-supplied fields."""
    table = MagicMock()
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import update_job

        update_job("MREC-5", status="done")
    kwargs = table.update_item.call_args.kwargs
    expr_names = kwargs["ExpressionAttributeNames"]
    assert "#updated_at" in expr_names


def test_update_job_passes_correct_key():
    """update_job targets the correct job_id in the DynamoDB Key."""
    table = MagicMock()
    with patch("app.services.job_store._table", return_value=table):
        from app.services.job_store import update_job

        update_job("MREC-99", status="error")
    kwargs = table.update_item.call_args.kwargs
    assert kwargs["Key"] == {"job_id": "MREC-99"}
