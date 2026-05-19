"""Verify the 120/min decorator is reachable via the real app.

We don't actually fire 120 requests — that's slow and tests the library, not
our wiring. We just verify the limit is registered in the limiter's route
registry so the rate limit was actually applied (catches refactor regressions).
"""
from __future__ import annotations

import pytest

from app.api.endpoints import report_a1, report_t1, report_t2, report_t3
from app.core.rate_limit import limiter  # noqa: F401

# The /generate handler function names per module.
_GENERATE_HANDLER = {
    "report_t1": "submit_t1_report_job",
    "report_t2": "submit_t2_report_job",
    "report_t3": "submit_t3_report_job",
    "report_a1": "submit_report_job",
}


@pytest.mark.unit
@pytest.mark.parametrize(
    "module",
    [report_t1, report_t2, report_t3, report_a1],
    ids=["t1", "t2", "t3", "a1"],
)
def test_generate_endpoint_has_rate_limit(module):
    """The /generate handler in each tier module must be limit-decorated."""
    short_name = module.__name__.split(".")[-1]
    handler_name = _GENERATE_HANDLER[short_name]
    route_key = f"{module.__name__}.{handler_name}"

    assert route_key in limiter._route_limits, (
        f"No rate limit registered for {route_key}. "
        f"Registered keys: {sorted(limiter._route_limits.keys())}"
    )

    # Verify the limit value is 120/minute
    limits = limiter._route_limits[route_key]
    limit_strings = [str(lim.limit) for lim in limits]
    assert any("120" in s for s in limit_strings), (
        f"Expected 120/minute limit on {route_key}, got: {limit_strings}"
    )
