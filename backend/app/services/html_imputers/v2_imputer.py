"""HTML imputer for MREC_Report_TEMPLATE_T1.

Thin wrapper around the shared DATA-block replacement logic, typed to the V2
schema.  The underlying regex replacement is identical to the baseline imputer;
the separate module exists so callers import a clearly versioned symbol and so
the V2 type is enforced at the call site.
"""

from collections.abc import Mapping
from typing import Any

from app.services.html_imputers.baseline_imputer import (
    inject_data_patch,
    populate_template_file,
    replace_data_block,
)
from app.types.baseline_report_template import ReportTemplateDataV2

TemplateDataInputV2 = Mapping[str, Any] | ReportTemplateDataV2


def replace_data_block_v2(template_html: str, data: TemplateDataInputV2) -> str:
    """Replace the ``const DATA = {...};`` block in a V2 template."""
    return replace_data_block(template_html, data)  # type: ignore[arg-type]


def inject_data_patch_v2(template_html: str, patch: TemplateDataInputV2) -> str:
    """Inject a partial update via ``Object.assign(DATA, patch)`` into a V2 template."""
    return inject_data_patch(template_html, patch)  # type: ignore[arg-type]


__all__ = [
    "TemplateDataInputV2",
    "replace_data_block_v2",
    "inject_data_patch_v2",
    "populate_template_file",  # re-exported; path-aware, works for both versions
]
