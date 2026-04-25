"""Unit tests for app.services.cpt — pure helpers (no IO)."""

import pandas as pd

from app.services.cpt import (
    check_cpt_in_ranges,
    flag_anchor_cpt_codes,
    generate_cpt_placeholders,
    get_top_cpt_df,
    parse_anchor_codes_filters,
)

# ── parse_anchor_codes_filters ────────────────────────────────────────────────


def test_parse_anchor_codes_filters_empty_string():
    ranges, individuals = parse_anchor_codes_filters("")
    assert ranges == []
    assert individuals == []


def test_parse_anchor_codes_filters_individual_codes_only():
    ranges, individuals = parse_anchor_codes_filters("99213, G0438, G0439")
    assert ranges == []
    assert individuals == ["99213", "G0438", "G0439"]


def test_parse_anchor_codes_filters_ranges_only():
    ranges, individuals = parse_anchor_codes_filters("99202-99215, G0438-G0439")
    assert ranges == [("99202", "99215"), ("G0438", "G0439")]
    assert individuals == []


def test_parse_anchor_codes_filters_mixed():
    ranges, individuals = parse_anchor_codes_filters("99202-99215, 99381, G0438-G0439")
    assert ranges == [("99202", "99215"), ("G0438", "G0439")]
    assert individuals == ["99381"]


def test_parse_anchor_codes_filters_em_dash_normalized():
    """Em-dash (–) should be normalized to hyphen (-) for ranges."""
    ranges, individuals = parse_anchor_codes_filters("99202–99215")
    assert ranges == [("99202", "99215")]
    assert individuals == []


def test_parse_anchor_codes_filters_skips_garbage():
    ranges, individuals = parse_anchor_codes_filters("???, 99213, !!!")
    assert ranges == []
    assert individuals == ["99213"]


# ── check_cpt_in_ranges ───────────────────────────────────────────────────────


def test_check_cpt_in_ranges_individual_match():
    assert check_cpt_in_ranges("99213", [], ["99213"]) is True


def test_check_cpt_in_ranges_range_match_low_end():
    assert check_cpt_in_ranges("99202", [("99202", "99215")], []) is True


def test_check_cpt_in_ranges_range_match_high_end():
    assert check_cpt_in_ranges("99215", [("99202", "99215")], []) is True


def test_check_cpt_in_ranges_no_match():
    assert check_cpt_in_ranges("00000", [("99202", "99215")], ["99213"]) is False


def test_check_cpt_in_ranges_alpha_range():
    assert check_cpt_in_ranges("G0438", [("G0438", "G0439")], []) is True
    assert check_cpt_in_ranges("G0440", [("G0438", "G0439")], []) is False


# ── flag_anchor_cpt_codes ─────────────────────────────────────────────────────


def test_flag_anchor_cpt_codes_sums_only_anchor_columns():
    df = pd.DataFrame(
        {
            "Procedure Volume: 99213": [10, 20],
            "Procedure Volume: 99999": [5, 5],
            "Procedure Volume: G0438": [1, 2],
        }
    )
    out_df, total = flag_anchor_cpt_codes(df, [("G0438", "G0439")], ["99213"])
    assert total == 10 + 20 + 1 + 2  # 99213 (anchor) + G0438 (anchor)
    assert out_df["Procedure Volume: 99213 - is_anchor"].iloc[0] == True  # noqa: E712
    assert out_df["Procedure Volume: 99999 - is_anchor"].iloc[0] == False  # noqa: E712
    assert out_df["Procedure Volume: G0438 - is_anchor"].iloc[0] == True  # noqa: E712


# ── get_top_cpt_df + generate_cpt_placeholders ────────────────────────────────


def test_get_top_cpt_df_sorts_descending():
    df = pd.DataFrame(
        {
            "Procedure Volume: 99213": [10, 5],
            "Procedure Volume: 99214": [100, 100],
        }
    )
    cpt_lookup = pd.DataFrame({"HCPCS": ["99213", "99214"], "DESCRIPTION": ["Est15", "Est25"]})
    top_df = get_top_cpt_df(df, cpt_lookup)
    assert list(top_df["cpt"]) == ["99214", "99213"]
    assert top_df.iloc[0]["cpt_count"] == 200
    assert top_df.iloc[0]["cpt_description"] == "Est25"


def test_generate_cpt_placeholders_formats_count_with_commas():
    top_df = pd.DataFrame({"cpt": ["99213"], "cpt_count": [12345], "cpt_description": ["Est15"]})
    placeholders = generate_cpt_placeholders(top_df)
    assert placeholders["{CPT_1}"] == "99213"
    assert placeholders["{CPT_1_desc}"] == "Est15"
    assert placeholders["{CPT_1_count}"] == "12,345"
