"""Unit tests for app.utils.common — severity scoring, population, tag generation."""

from app.types.baseline_report_template import CptRowV2
from app.utils.common import (
    generate_tags,
    get_anchor_cpt_severity_scoring,
    get_geriatric_population,
    get_pediatric_population,
    get_population_severity_scoring,
)

# ── get_population_severity_scoring ──────────────────────────────────────────


def test_severity_underserved_when_actual_lt_half_target():
    label, _ = get_population_severity_scoring(current_avg_provider_per_100k=10.0, target_avg_provider_per_100k=30.0)
    assert label == "Underserved - High Priority"


def test_severity_moderate_gap_between_50_and_80():
    label, _ = get_population_severity_scoring(current_avg_provider_per_100k=20.0, target_avg_provider_per_100k=30.0)
    assert label == "Moderate Gap"


def test_severity_saturated_at_80_or_above():
    label, _ = get_population_severity_scoring(current_avg_provider_per_100k=25.0, target_avg_provider_per_100k=30.0)
    assert label == "Saturated"


# ── get_anchor_cpt_severity_scoring ──────────────────────────────────────────


def test_anchor_severity_high_potential_when_actual_exceeds_target():
    diff, label, _ = get_anchor_cpt_severity_scoring(target_anchor_visits_count=1000, actual_anchor_visits_count=1500)
    assert diff == 500
    assert label == "High Potential"


def test_anchor_severity_balanced_when_equal():
    diff, label, _ = get_anchor_cpt_severity_scoring(target_anchor_visits_count=1000, actual_anchor_visits_count=1000)
    assert diff == 0
    assert label == "Balanced Market"


def test_anchor_severity_high_risk_when_actual_below_target():
    diff, label, _ = get_anchor_cpt_severity_scoring(target_anchor_visits_count=1000, actual_anchor_visits_count=400)
    assert diff == -600
    assert label == "Low Potential / High Risk"


# ── pediatric / geriatric population ─────────────────────────────────────────


def _make_demographics() -> dict:
    """Symmetric small population — easy arithmetic."""
    age_keys = [
        "Total", "0-4", "5-9", "10-14", "15-17", "18-19", "20", "21", "22-24",
        "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
        "60-61", "62-64", "65-66", "67-69", "70-74", "75-79", "80-84", "85-1000",
    ]
    return {
        "M": {k: (0 if k == "Total" else 10) for k in age_keys},
        "F": {k: (0 if k == "Total" else 10) for k in age_keys},
        "Total": 0,
    }


def test_pediatric_population_sums_under_24():
    demo = _make_demographics()
    pop = get_pediatric_population(demo)
    # ranges with upper bound <= 24: 0-4, 5-9, 10-14, 15-17, 18-19, 20, 21, 22-24 → 8 ranges × (10M + 10F) = 160
    assert pop == 8 * 20


def test_geriatric_population_sums_60_plus():
    demo = _make_demographics()
    pop = get_geriatric_population(demo)
    # ranges with lower bound >= 60: 60-61, 62-64, 65-66, 67-69, 70-74, 75-79, 80-84, 85-1000 → 8 × 20 = 160
    assert pop == 8 * 20


# ── generate_tags ────────────────────────────────────────────────────────────


def _row(code: str, peer: str, client: str, diff_volume: int) -> CptRowV2:
    return CptRowV2(code=code, peerAvgVolume=peer, clientVolume=client, diffVolume=diff_volume)


def test_generate_tags_always_includes_2024_data_tag():
    tags = generate_tags([])
    assert any(t.text == "2024 Procedures Data" for t in tags)


def test_generate_tags_quick_win_tag_when_peer_exceeds_client():
    rows = [_row("99213", "100", "50", 50), _row("99214", "10", "20", -10)]
    tags = generate_tags(rows)
    quickwin = [t for t in tags if "Quick-Win" in t.text]
    assert len(quickwin) == 1
    assert "1" in quickwin[0].text


def test_generate_tags_top_gap_picks_highest_diff_volume():
    rows = [_row("99213", "100", "50", 50), _row("99214", "100", "10", 90)]
    tags = generate_tags(rows)
    top = [t for t in tags if "Top Gap" in t.text]
    assert len(top) == 1
    assert top[0].text.startswith("99214")


def test_generate_tags_no_quickwin_when_client_meets_peer():
    rows = [_row("99213", "100", "200", -100)]
    tags = generate_tags(rows)
    assert not any("Quick-Win" in t.text for t in tags)
    assert not any("Top Gap" in t.text for t in tags)
