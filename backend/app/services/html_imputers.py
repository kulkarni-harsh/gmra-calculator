"""HTML template imputer — injects Python data into the ``const DATA = {...};`` block.

Single module replacing the old ``html_imputers/`` sub-package
(baseline_imputer + v2_imputer + v3_imputer).

Template selection
------------------
Use ``render_report(tier, data)`` as the single call-site for rendering.
It reads the right template for the tier and injects *data* in one step.

    render_report("T1", report_data)   # active — market-entry / address-only report
    render_report("A1", report_data)   # archived — provider NPI report

Adding a new tier only requires adding one entry to ``_TIER_TEMPLATES``.
"""

import json
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.types.baseline_report_template import ReportTemplateData, ReportTemplateDataV2

# ── Tier → template filename mapping ─────────────────────────────────────────
# All report-tier names are defined here.  Generators reference the tier string;
# the file on disk is resolved in one place.

_TIER_TEMPLATES: dict[str, str] = {
    "T1": "MREC_Report_TEMPLATE_T1.html",  # active — market-entry / address-only report
    "A1": "MREC_Report_TEMPLATE_A1.html",  # archived — provider NPI report
}

# ── Core regex ────────────────────────────────────────────────────────────────

DATA_BLOCK_PATTERN = re.compile(
    r"const\s+DATA\s*=\s*\{.*?\n\};",
    flags=re.DOTALL,
)

# ── Type alias ────────────────────────────────────────────────────────────────

TemplateDataInput = Mapping[str, Any] | ReportTemplateData | ReportTemplateDataV2


# ── Internal helpers ──────────────────────────────────────────────────────────


def _normalize(data: TemplateDataInput) -> dict[str, Any]:
    if isinstance(data, Mapping):
        return dict(data)
    if is_dataclass(data):
        raw = asdict(data)  # type: ignore[arg-type]
        if isinstance(raw, dict):
            return raw
    raise TypeError("`data` must be a mapping or a dataclass instance.")


def _to_js_object(data: TemplateDataInput) -> str:
    payload = json.dumps(_normalize(data), indent=2, ensure_ascii=False)
    # Replace "</" with "<\/" so a data value containing "</script>" cannot
    # accidentally close the surrounding <script> tag and break the page.
    # json.dumps handles all other JSON escaping; this is the only HTML-specific risk.
    return payload.replace("</", "<\\/")


# ── Public API ────────────────────────────────────────────────────────────────


def replace_data_block(template_html: str, data: TemplateDataInput) -> str:
    """Replace ``const DATA = {...};`` in the HTML template with *data*."""
    replacement = f"const DATA = {_to_js_object(data)};"
    updated, count = DATA_BLOCK_PATTERN.subn(replacement, template_html, count=1)
    if count != 1:
        raise ValueError("Could not find exactly one `const DATA = {...};` block in template HTML.")
    return updated


def inject_data_patch(template_html: str, patch: TemplateDataInput) -> str:
    """Inject ``Object.assign(DATA, patch)`` before ``</script>`` for partial updates."""
    match = DATA_BLOCK_PATTERN.search(template_html)
    if match is None:
        raise ValueError("Could not find `const DATA = {...};` block in template HTML.")
    close_idx = template_html.find("</script>", match.end())
    if close_idx == -1:
        raise ValueError("Could not find closing </script> tag after DATA block.")
    injection = f"\nObject.assign(DATA, {_to_js_object(patch)});\n"
    return template_html[:close_idx] + injection + template_html[close_idx:]


def render_report(tier: str, data: TemplateDataInput) -> str:
    """Read the template for *tier* and inject *data*.  One-stop rendering call.

    ``tier`` must be a key in ``_TIER_TEMPLATES`` (e.g. ``"T1"``, ``"A1"``).
    Raises ``ValueError`` with a clear message for unknown tiers.
    """
    if tier not in _TIER_TEMPLATES:
        raise ValueError(f"Unknown report tier {tier!r}. Valid tiers: {sorted(_TIER_TEMPLATES)}")
    filename = _TIER_TEMPLATES[tier]
    template_html = (settings.TEMPLATES_DIR / filename).read_text(encoding="utf-8")
    return replace_data_block(template_html, data)


def populate_template_file(
    template_path: str | Path,
    output_path: str | Path,
    data: TemplateDataInput,
    mode: str = "replace",
) -> Path:
    """Read *template_path*, populate with *data*, write to *output_path*.

    ``mode='replace'`` replaces the full DATA block.
    ``mode='patch'`` injects a partial ``Object.assign`` update.
    """
    html = Path(template_path).read_text(encoding="utf-8")
    if mode == "replace":
        out = replace_data_block(html, data)
    elif mode == "patch":
        out = inject_data_patch(html, data)
    else:
        raise ValueError("`mode` must be 'replace' or 'patch'.")
    result = Path(output_path)
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(out, encoding="utf-8")
    return result


__all__ = [
    "render_report",
    "replace_data_block",
    "inject_data_patch",
    "populate_template_file",
    "TemplateDataInput",
]
