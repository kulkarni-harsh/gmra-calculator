"""HTML imputer for MREC_Report_TEMPLATE_T0.

Thin wrapper around the shared DATA-block replacement logic, typed to the V2
schema (V3 reuses the same dataclass with additional optional fields).
"""

from collections.abc import Mapping
from typing import Any

from app.services.html_imputers.baseline_imputer import (
    inject_data_patch,
    populate_template_file,
    replace_data_block,
)
from app.types.baseline_report_template import ReportTemplateDataV2

TemplateDataInputV3 = Mapping[str, Any] | ReportTemplateDataV2


def replace_data_block_v3(template_html: str, data: TemplateDataInputV3) -> str:
    """Replace the ``const DATA = {...};`` block in a V3 template."""
    return replace_data_block(template_html, data)  # type: ignore[arg-type]


def inject_data_patch_v3(template_html: str, patch: TemplateDataInputV3) -> str:
    """Inject a partial update via ``Object.assign(DATA, patch)`` into a V3 template."""
    return inject_data_patch(template_html, patch)  # type: ignore[arg-type]


__all__ = [
    "TemplateDataInputV3",
    "replace_data_block_v3",
    "inject_data_patch_v3",
    "populate_template_file",  # re-exported; path-aware, works for both versions
]
