# backend/tests/test_worker_idle.py
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


def test_worker_exits_after_3_empty_polls_when_queue_confirmed_empty():
    with patch("app.worker.receive_jobs", return_value=[]) as mock_receive, \
         patch("app.worker.get_queue_depth", return_value=0) as mock_depth, \
         patch("app.worker.delete_message"):
        state = MagicMock()

        async def run():
            from app.worker import main_loop
            await main_loop(state, max_idle_polls=3)

        asyncio.run(run())

    assert mock_receive.call_count == 3
    assert mock_depth.call_count == 1


def test_worker_resets_idle_counter_when_depth_nonzero():
    # First 3 empty polls → depth check returns 1 (reset) → 3 more empty polls → depth 0 → exit
    with patch("app.worker.receive_jobs", return_value=[]) as mock_receive, \
         patch("app.worker.get_queue_depth", side_effect=[1, 0]) as mock_depth, \
         patch("app.worker.delete_message"):
        state = MagicMock()

        async def run():
            from app.worker import main_loop
            await main_loop(state, max_idle_polls=3)

        asyncio.run(run())

    assert mock_receive.call_count == 6
    assert mock_depth.call_count == 2


def test_worker_resets_idle_counter_on_message():
    msg = {"Body": '{"job_id": "MERC-1"}', "ReceiptHandle": "r1"}
    # Return a message on the first call, then empty × 3
    with patch("app.worker.receive_jobs", side_effect=[[msg], [], [], []]) as mock_receive, \
         patch("app.worker.get_queue_depth", return_value=0), \
         patch("app.worker.delete_message"), \
         patch("app.worker.process_job", new_callable=AsyncMock) as mock_process:
        state = MagicMock()

        async def run():
            from app.worker import main_loop
            await main_loop(state, max_idle_polls=3)

        asyncio.run(run())

    mock_process.assert_called_once_with("MERC-1", state)
    assert mock_receive.call_count == 4  # 1 message + 3 empty → exit
