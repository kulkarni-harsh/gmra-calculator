"""
Convert an HTML string to PDF bytes using Playwright (Chromium headless).

Async API is used so this works inside an asyncio event loop (e.g. the SQS worker).

Docker / ECS — add to your Dockerfile:
    RUN uv run playwright install chromium --with-deps
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

# Milliseconds to wait after networkidle for setTimeout-driven rendering
_SETTLE_MS: int = 1_500

# CSS reference pixel density: 96 px = 1 inch
_PX_PER_INCH: float = 96.0


async def html_to_pdf(html: str) -> bytes:
    """Render an HTML string to a single-page PDF. Returns raw PDF bytes."""
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8", delete=False) as fh:
        fh.write(html)
        tmp = Path(fh.name)
    try:
        return await _render(f"file://{tmp.resolve()}")
    finally:
        tmp.unlink(missing_ok=True)


# ── internal ──────────────────────────────────────────────────────────────────


async def _measure(page) -> tuple[float, float]:
    """Return (width_in, height_in) of the fully-rendered page."""
    dims: dict = await page.evaluate("""() => {
        const el = document.querySelector('.page');
        if (el) {
            const r    = el.getBoundingClientRect();
            const s    = getComputedStyle(document.body);
            const padV = (parseFloat(s.paddingTop)    || 0)
                       + (parseFloat(s.paddingBottom) || 0);
            const padH = (parseFloat(s.paddingLeft)   || 0)
                       + (parseFloat(s.paddingRight)  || 0);
            return { width: Math.ceil(r.width + padH), height: Math.ceil(r.height + padV) };
        }
        return {
            width:  Math.max(document.body.scrollWidth,
                             document.documentElement.scrollWidth),
            height: Math.max(document.body.scrollHeight,
                             document.documentElement.scrollHeight),
        };
    }""")
    return dims["width"] / _PX_PER_INCH, dims["height"] / _PX_PER_INCH


async def _render(url: str) -> bytes:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            args=[
                "--no-sandbox",  # required when running as root in ECS
                "--disable-dev-shm-usage",  # ECS tasks have a small /dev/shm by default
                "--disable-gpu",
            ]
        )
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(_SETTLE_MS)

        w_in, h_in = await _measure(page)

        pdf_bytes: bytes = await page.pdf(
            print_background=True,
            width=f"{w_in}in",
            height=f"{h_in}in",
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        await browser.close()
        return pdf_bytes
