import json
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from app.types.baseline_report_template import ReportTemplateData

DATA_BLOCK_PATTERN = re.compile(
    r"const\s+DATA\s*=\s*\{.*?\n\};",
    flags=re.DOTALL,
)

TemplateDataInput = Mapping[str, Any] | ReportTemplateData


def _normalize_data(data: TemplateDataInput) -> dict[str, Any]:
    """Convert ReportTemplateData (or any mapping) into a plain dict for JSON serialization."""
    if isinstance(data, Mapping):
        return dict(data)
    if is_dataclass(data):
        raw = asdict(data)
        if isinstance(raw, dict):
            return raw
    raise TypeError("`data` must be a mapping or ReportTemplateData dataclass instance.")


def _to_javascript_object(data: TemplateDataInput) -> str:
    """Serialize a Python mapping into a JS-safe object literal string."""
    payload = json.dumps(_normalize_data(data), indent=2, ensure_ascii=False)
    # Prevent accidental closing of the current script tag.
    return payload.replace("</", "<\\/")


def replace_data_block(template_html: str, data: TemplateDataInput) -> str:
    """
    Replace the `const DATA = {...};` block in the HTML template.

    Pass the full DATA payload expected by your HTML template.
    """
    js_object = _to_javascript_object(data)
    replacement = f"const DATA = {js_object};"

    updated_html, replacements = DATA_BLOCK_PATTERN.subn(replacement, template_html, count=1)
    if replacements != 1:
        raise ValueError("Could not find exactly one `const DATA = {...};` block in template HTML.")
    return updated_html


def inject_data_patch(template_html: str, patch: TemplateDataInput) -> str:
    """
    Inject `Object.assign(DATA, patch)` before the DATA script closes.

    Use this when you want partial updates instead of replacing the full DATA block.
    """
    match = DATA_BLOCK_PATTERN.search(template_html)
    if match is None:
        raise ValueError("Could not find `const DATA = {...};` block in template HTML.")

    script_close_idx = template_html.find("</script>", match.end())
    if script_close_idx == -1:
        raise ValueError("Could not find closing </script> tag after DATA block.")

    patch_object = _to_javascript_object(patch)
    injection = f"\nObject.assign(DATA, {patch_object});\n"
    return template_html[:script_close_idx] + injection + template_html[script_close_idx:]


def populate_template_file(
    template_path: str | Path,
    output_path: str | Path,
    data: TemplateDataInput,
    mode: str = "replace",
) -> Path:
    """
    Read template HTML and populate it with Python data.

    `mode="replace"` expects full DATA payload and replaces `const DATA = {...};`.
    `mode="patch"` performs a partial update via `Object.assign(DATA, patch)`.
    """
    template_file = Path(template_path)
    output_file = Path(output_path)

    html = template_file.read_text(encoding="utf-8")
    if mode == "replace":
        populated_html = replace_data_block(template_html=html, data=data)
    elif mode == "patch":
        populated_html = inject_data_patch(template_html=html, patch=data)
    else:
        raise ValueError("`mode` must be either 'replace' or 'patch'.")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(populated_html, encoding="utf-8")
    return output_file
