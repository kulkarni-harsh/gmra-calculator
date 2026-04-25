"""Guardrails: production code uses logging, not print()."""

import inspect

from app.services import cpt as svc_cpt
from app.services import fee_schedule as svc_fee_schedule
from app.services import google_maps as svc_gmaps
from app.services import ppt as svc_ppt
from app.services import specialty as svc_specialty
from app.utils import common as utils_common
from app.utils import validator as utils_validator


def _assert_no_print(module) -> None:
    src = inspect.getsource(module)
    # Allow `# print(` in commented-out debug; reject live `print(`.
    for line in src.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        assert "print(" not in stripped, f"{module.__name__}: live print found → {line!r}"


def test_no_prints_in_utils_common():
    _assert_no_print(utils_common)


def test_no_prints_in_utils_validator():
    _assert_no_print(utils_validator)


def test_no_prints_in_services_cpt():
    _assert_no_print(svc_cpt)


def test_no_prints_in_services_specialty():
    _assert_no_print(svc_specialty)


def test_no_prints_in_services_google_maps():
    _assert_no_print(svc_gmaps)


def test_no_prints_in_services_ppt():
    _assert_no_print(svc_ppt)


def test_fee_schedule_has_no_commented_print_block():
    """Cleanup: stale commented-out print() debug lines should be deleted."""
    src = inspect.getsource(svc_fee_schedule)
    assert src.count("# print(") == 0, "remove stale commented print() lines"
