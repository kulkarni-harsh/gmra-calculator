"""
Binary-search the AlphaSophia procedure API to find the highest req/s that produces
zero 504s, then validates with a full run across all HCP IDs × CPT codes.

Run from backend/:
    uv run python scripts/test_alphasophia_rate.py
"""

import asyncio
import json
import logging
import os
import random
import time
from pathlib import Path

import httpx
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

API_KEY = os.environ["ALPHASOPHIA_API_KEY"]
BASE_URL = "https://api.alphasophia.com"
TIMEOUT = httpx.Timeout(connect=20, read=60, write=20, pool=600)

HCP_IDS = [
    5155085,
    3956616,
    1521147,
    2859700,
    2809229,
    3064252,
    1539596,
    3018112,
    2719681,
    3024709,
    1041595,
    302613,
    532980,
    985059,
    2520073,
    4502207,
    1140894,
    437705,
    1824752,
    1900713,
    4516648,
    4902112,
    5546538,
    2531178,
    3082373,
    3509755,
    265581,
    990231,
    580048,
    1775468,
    2178407,
    753530,
    8233,
    1239305,
    1195965,
    5059901,
    3663499,
    3468890,
    4854478,
    3414991,
    3131495,
    3446192,
    2366178,
    1240499,
    5597353,
    852779,
    4779162,
    3811978,
    3493369,
    1790418,
    1724316,
    5398735,
    1649822,
    1280579,
    3014571,
    4022377,
    2055341,
    5607281,
    5031697,
    1417530,
    3925012,
    978376,
    945295,
    1274347,
    2413488,
    5052983,
    1324008,
    286539,
    3856508,
    615195,
    2465283,
    3707922,
    5492184,
    3011878,
    1700896,
    1703505,
    5166751,
    5562003,
    3064195,
    1430896,
    5373079,
    1874019,
    3610667,
    2796653,
    2924669,
    3769125,
    289838,
    5170664,
    232150,
    1629702,
    827178,
    2364022,
    1287307,
    3234839,
    1974794,
    5564401,
    2631491,
    2286522,
    4212786,
    3511699,
    2967722,
    4957733,
    4787682,
    17207,
    1385936,
    2549895,
    5595872,
    4213323,
    5101679,
    1058942,
    2109670,
    3323805,
    2366266,
    5148398,
    77830,
    3756946,
    3206089,
    5098425,
    2567393,
    3909046,
    3319224,
    3409122,
    3565520,
    1623513,
    1723575,
    4383125,
    3035834,
    5351913,
    4533857,
    5603140,
    1721944,
    3364731,
    4274783,
    4843020,
    1350039,
    2430229,
    5507783,
    3479887,
    3314576,
    4355835,
    2072385,
    5306974,
    5441670,
    4517362,
    786221,
    4602133,
    919387,
    1331178,
    1914984,
    3313014,
    563778,
    2550175,
    1445918,
    5501583,
    2282384,
    5651348,
    312496,
    571262,
    1325505,
    4852729,
    4212652,
    4163032,
    5375057,
    4856558,
    3608429,
]


def load_cpt_codes() -> list[str]:
    path = Path(__file__).parent.parent / "resources/lookups/anchor_cpt_lookup.json"
    d = json.loads(path.read_text())["through_the_door_cpt_codes"]
    return (
        [i["code"] for i in d["em_office_visits"]["codes"]]
        + [i["code"] for i in d["preventive_visits"]["codes"]]
        + [i["code"] for i in d["obgyn_specific"]["codes"]]
    )


async def _fetch(
    client: httpx.AsyncClient,
    limiter: AsyncLimiter,
    hcp_id: int,
    cpt_code: str,
) -> int | str:
    async with limiter:
        try:
            r = await client.get(
                "/v1/profile/hcp/procedure/",
                params={"id": hcp_id, "all-payor": "true", "page": 1, "pageSize": 15, "time": "2024", "code": cpt_code},
                headers={"x-api-key": API_KEY, "Accept": "application/json"},
                timeout=TIMEOUT,
            )
            return r.status_code
        except httpx.TimeoutException:
            return "timeout"
        except Exception as exc:
            return f"err:{type(exc).__name__}"


async def run_batch(rpm: int, pairs: list[tuple[int, str]]) -> dict:
    # Each round sends exactly `rpm` requests spread evenly over 60 seconds —
    # one full minute of sustained load, matching how AlphaSophia enforces its limit.
    limiter = AsyncLimiter(max_rate=rpm, time_period=60)
    async with httpx.AsyncClient(base_url=BASE_URL, limits=httpx.Limits(max_connections=300)) as client:
        t0 = time.monotonic()
        results = await asyncio.gather(*[_fetch(client, limiter, hid, code) for hid, code in pairs])
        elapsed = time.monotonic() - t0

    counts: dict[str, int] = {}
    for r in results:
        key = str(r)
        counts[key] = counts.get(key, 0) + 1

    return {
        "rpm": rpm,
        "total": len(results),
        "ok": counts.get("200", 0),
        "504s": counts.get("504", 0),
        "timeouts": counts.get("timeout", 0),
        "other": {k: v for k, v in counts.items() if k not in ("200", "504", "timeout")},
        "elapsed": round(elapsed, 1),
    }


def log_result(r: dict, label: str = "") -> None:
    pct_504 = 100 * r["504s"] / r["total"] if r["total"] else 0
    status = f"✗ {r['504s']} 504s ({pct_504:.1f}%)" if r["504s"] else "✓ clean"
    log.info(
        "%s[%d rpm] %s  |  ok=%d  timeout=%d  other=%s  elapsed=%.0fs",
        f"{label} " if label else "",
        r["rpm"],
        status,
        r["ok"],
        r["timeouts"],
        r["other"] or "{}",
        r["elapsed"],
    )


async def binary_search(all_pairs: list[tuple[int, str]]) -> int:
    # Sample size = midpoint of range so each round tests exactly one minute of load.
    low, high = 100, 2000
    best_safe = low
    cooldown = 90  # wait one full rate-limit window after a 504 before next test

    log.info("Binary search: req/minute range %d–%d, one minute of load per round", low, high)

    while high - low > 10:
        mid = (low + high) // 2
        rng = random.Random(42)
        sample = rng.sample(all_pairs, min(mid, len(all_pairs)))

        log.info("--- Testing %d rpm (%d requests over ~60s) ---", mid, len(sample))
        result = await run_batch(mid, sample)
        log_result(result)

        if result["504s"] == 0:
            best_safe = mid
            low = mid
            await asyncio.sleep(5)
        else:
            high = mid
            log.info("Cooling down %ds (one rate-limit window)...", cooldown)
            await asyncio.sleep(cooldown)

    log.info("=== Search complete. Best safe rate: %d rpm ===", best_safe)
    return best_safe


async def full_run(rpm: int, all_pairs: list[tuple[int, str]]) -> None:
    est = len(all_pairs) / rpm * 60
    log.info("Full run: %d requests at %d rpm — est. %.0fs (%.1f min)", len(all_pairs), rpm, est, est / 60)
    result = await run_batch(rpm, all_pairs)
    log_result(result, label="FULL")
    if result["504s"]:
        log.warning("Full run had 504s — consider dropping to %d rpm", int(rpm * 0.8))
    else:
        log.info("Full run clean. Set _ALPHASOPHIA_RPM = %d in alphasophia.py", rpm)


async def main() -> None:
    cpt_codes = load_cpt_codes()
    all_pairs = [(hid, code) for hid in HCP_IDS for code in cpt_codes]
    log.info(
        "%d HCP IDs × %d CPT codes = %d total pairs",
        len(HCP_IDS),
        len(cpt_codes),
        len(all_pairs),
    )

    safe_rpm = await binary_search(all_pairs)

    log.info("")
    log.info("=== Validating with full run at %d rpm ===", safe_rpm)
    await full_run(safe_rpm, all_pairs)


if __name__ == "__main__":
    asyncio.run(main())
