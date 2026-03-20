import logging

import pandas as pd

from app.core.config import settings
from app.core.types import SexAgeCounts
from app.types.baseline_report_template import CptRowV2, Tag

_RVU_QPP_FILE = settings.LOOKUP_DIR / "PPRRvu2026_Jan_QPP.csv"
_RVU_NONQPP_FILE = settings.LOOKUP_DIR / "PPRRvu2026_Jan_nonQPP.csv"
_GPCI_FILE = settings.LOOKUP_DIR / "GPCI2026.csv"
_CONVERSION_FACTOR = 33.5675  # CY 2026 national conversion factor (fallback)


def get_population_severity_scoring(
    current_avg_provider_per_100k: float, target_avg_provider_per_100k: float
) -> tuple[str, str]:
    """Determine severity scoring based on provider ratios and provide rationale"""
    if current_avg_provider_per_100k < 0.5 * target_avg_provider_per_100k:
        return (
            "Underserved - High Priority",
            "Current provider ratio is < 50% of the target, indicating a significant shortage.",
        )
    elif current_avg_provider_per_100k < 0.8 * target_avg_provider_per_100k:
        return (
            "Moderate Gap",
            "Current provider ratio is between 50% and 80% of the target, indicating a moderate gap.",
        )
    else:
        return (
            "Saturated",
            "Current provider ratio is >= 80% of the target, indicating saturation.",
        )


def get_anchor_cpt_severity_scoring(
    target_anchor_visits_count: int,
    actual_anchor_visits_count: int,
) -> tuple[int, str, str]:
    """Determine severity scoring based on anchor CPT counts and provide rationale"""
    visits_diff = int(actual_anchor_visits_count - target_anchor_visits_count)
    # If actual visits are less than target visits, then it means that current providers are enough to handle the demand
    # If actual visits are more than target visits, then it means that there is a gap in the market
    capacity_percent = round((actual_anchor_visits_count / target_anchor_visits_count) * 100, 1)
    print(
        f"CPT Stats: Target={target_anchor_visits_count}, "
        f"Actual={actual_anchor_visits_count} visits_diff={visits_diff} "
        f"capacity_percent={capacity_percent}%"
    )
    print(f"Anchor CPT visits capacity percent: {capacity_percent}%")
    if visits_diff < 0:
        return (
            visits_diff,
            "Low Potential / High Risk",
            f"""Competition at {capacity_percent}% capacity with {abs(visits_diff):,}"""
            + """ "empty chair" visits available. """
            + "Existing surplus creates high risk for a new entrant.",
        )
    elif visits_diff == 0:
        return (
            visits_diff,
            "Balanced Market",
            "Market is balanced with no surplus or deficit in anchor CPT visits.",
        )
    else:
        return (
            visits_diff,
            "High Potential",
            f"""Market at {capacity_percent}% capacity with {visits_diff:,} visits exceeding benchmarks. """
            + "This overflow creates a clear entry point for a new office.",
        )


def get_provider_density(specialty_lookup: dict, specialty_name: str, state: str) -> float | None:
    """Return providers per 100k population for the given specialty and state, or None if not found."""
    for val in specialty_lookup.values():
        if val["description"].strip().lower() == specialty_name.strip().lower():
            states: dict = val.get("states", {})
            return states.get(state.strip().upper())
    return None


def get_taxonomy_codes(specialty_lookup: dict, specialty_name: str) -> list[str]:
    """Return taxonomy codes for the given specialty name (case-insensitive match)."""
    for val in specialty_lookup.values():
        if val["description"].strip().lower() == specialty_name.strip().lower():
            return val["taxonomy_codes"]
    logging.warning("Specialty '%s' not found in specialty_map; proceeding with empty taxonomy codes.", specialty_name)
    return []


def get_source_tabs(specialty_lookup: dict, specialty_name: str) -> list[str]:
    """Return source_tabs (dashboard tab names) for the given specialty (case-insensitive match)."""
    for val in specialty_lookup.values():
        if val["description"].strip().lower() == specialty_name.strip().lower():
            return val.get("source_tabs", [])
    return []


def get_anchor_cpt_codes(anchor_cpt_lookup: dict, specialty_name: str) -> list[str]:
    """Return anchor CPT codes for the given specialty name (case-insensitive match)."""
    # "medicare_wellness": {
    #   "label": "Medicare Annual Wellness Visits",
    #   "codes": [
    #     { "code": "G0438", "description": "Annual wellness visit, initial" },
    #     { "code": "G0439", "description": "Annual wellness visit, subsequent" }
    #   ]
    # },
    anchor_cpt_codes = (
        [i["code"] for i in anchor_cpt_lookup["through_the_door_cpt_codes"]["em_office_visits"]["codes"]]
        + [i["code"] for i in anchor_cpt_lookup["through_the_door_cpt_codes"]["preventive_visits"]["codes"]]
        # + [i["code"] for i in anchor_cpt_lookup["through_the_door_cpt_codes"]["medicare_wellness"]["codes"]]
    )
    if "Gynecolog" in specialty_name:
        logging.debug(f"Adding obgyn-specific anchor CPT codes: {specialty_name}")
        anchor_cpt_codes += [
            i["code"] for i in anchor_cpt_lookup["through_the_door_cpt_codes"]["obgyn_specific"]["codes"]
        ]
    return anchor_cpt_codes


def get_anchor_cpt_patient_type_map(anchor_cpt_lookup: dict) -> dict[str, str]:
    """Return a mapping of CPT code → patient type ("New Patient" | "Established")."""
    result: dict[str, str] = {}
    for group in anchor_cpt_lookup.get("through_the_door_cpt_codes", {}).values():
        for entry in group.get("codes", []):
            if "patient_type" in entry:
                result[entry["code"]] = entry["patient_type"]
    return result


# ---------------------------------------------------------------------------
# Fee schedule loaders — called once at startup, stored on app.state
# ---------------------------------------------------------------------------


def _parse_rvu_csv(path) -> pd.DataFrame:
    """Parse a CMS RVU CSV (QPP or nonQPP) into a normalised DataFrame."""
    try:
        df = pd.read_csv(path, skiprows=9, header=0, low_memory=False)
    except FileNotFoundError:
        logging.error("RVU file not found: %s", path)
        return pd.DataFrame()

    df = df.rename(
        columns={
            "HCPCS": "code",
            "RVU": "work",
            "PE RVU": "pe_nonfac",
            "PE RVU.1": "pe_fac",
            "RVU.1": "mp",
            "FACTOR": "cf",
        }
    )
    # Prefer base-code rows (no modifier) over modifier-specific rows
    df["_no_mod"] = df["MOD"].isna() | (df["MOD"].astype(str).str.strip() == "")
    df = df.sort_values("_no_mod", ascending=False)
    df = df[["code", "work", "pe_nonfac", "pe_fac", "mp", "cf"]].copy()
    df["code"] = df["code"].astype(str).str.strip()
    for col in ["work", "pe_nonfac", "pe_fac", "mp", "cf"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df.loc[df["cf"] == 0.0, "cf"] = _CONVERSION_FACTOR
    return df.drop_duplicates(subset="code", keep="first")


def _build_rvu_table() -> dict[str, dict]:
    """Return {hcpcs_code: {work, pe_nonfac, pe_fac, mp, cf}} mapping.

    QPP codes are loaded first. nonQPP codes (e.g. preventive medicine codes
    99381-99396 which are non-covered by traditional Medicare but carry valid
    RVU values used by commercial payers) fill in any gaps.
    """
    qpp_df = _parse_rvu_csv(_RVU_QPP_FILE)
    nonqpp_df = _parse_rvu_csv(_RVU_NONQPP_FILE)

    if qpp_df.empty and nonqpp_df.empty:
        return {}

    # QPP rows take priority; nonQPP fills in codes absent from QPP
    combined = pd.concat([qpp_df, nonqpp_df], ignore_index=True)
    combined = combined.drop_duplicates(subset="code", keep="first")

    qpp_count = len(qpp_df)
    nonqpp_extra = len(combined) - qpp_count
    logging.debug("RVU table: %d QPP codes + %d nonQPP-only codes", qpp_count, nonqpp_extra)

    return combined.set_index("code")[["work", "pe_nonfac", "pe_fac", "mp", "cf"]].to_dict("index")


def _build_gpci_table() -> dict[str, dict]:
    """Return {state_abbr: {pw, pe, mp}} mapping (averaged across localities)."""
    try:
        df = pd.read_csv(_GPCI_FILE, skiprows=2, header=0)
    except FileNotFoundError:
        logging.error("GPCI file not found: %s", _GPCI_FILE)
        return {}

    df = df.rename(
        columns={
            "State": "state",
            "2026 PW GPCI (with 1.0 Floor)": "pw",
            "2026 PE GPCI": "pe",
            "2026 MP GPCI": "mp",
        }
    )
    df = df[["state", "pw", "pe", "mp"]].copy()
    df["state"] = df["state"].astype(str).str.strip().str.upper()
    for col in ["pw", "pe", "mp"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    agg = df.groupby("state")[["pw", "pe", "mp"]].mean()
    return agg.to_dict("index")


def load_fee_schedule_tables() -> tuple[dict[str, dict], dict[str, dict]]:
    """Parse CSVs and return (rvu_table, gpci_table) for storage on app.state.

    Call once from the FastAPI lifespan.
    """
    rvu_table = _build_rvu_table()
    gpci_table = _build_gpci_table()
    logging.info("Fee schedule loaded: %d CPT codes, %d states", len(rvu_table), len(gpci_table))
    return rvu_table, gpci_table


def get_pediatric_population(sex_age_counts_dict: SexAgeCounts) -> int:
    """Returns the total pediatric population (ages 0-24)."""
    pedatric_pop = 0
    for age_range in sex_age_counts_dict["M"].keys():
        if age_range == "Total":
            continue
        if int(age_range.split("-")[::-1][0]) <= 24:
            pedatric_pop += sex_age_counts_dict["M"][age_range] + sex_age_counts_dict["F"][age_range]
    return pedatric_pop


def get_geriatric_population(sex_age_counts_dict: SexAgeCounts) -> int:
    """Returns the total geriatric population (ages 60+)."""
    geriatric_pop = 0
    for age_range in sex_age_counts_dict["M"].keys():
        if age_range == "Total":
            continue
        if int(age_range.split("-")[0]) >= 60:
            geriatric_pop += sex_age_counts_dict["M"][age_range] + sex_age_counts_dict["F"][age_range]
    return geriatric_pop


def generate_tags(
    cpt_rows: list[CptRowV2],
):
    """Generate tags for the report.

    Args
    ----
    cpt_rows: list[CptRowV2]
        List of CPT codes with clientVolume, peerAvgVolume, and totalVolume.

    Returns
    -------
    tags_list: list[Tag]
        List of tags for the report.
    """
    tags_list = [Tag(text="2025 Procedures Data", color="sky")]

    # Get count of CPT codes with peerAvgVolume > clientVolume
    potential_cpt_count = 0
    quick_win_top_code = None
    for _cpt in cpt_rows:
        if (
            _cpt.peerAvgVolume
            and _cpt.clientVolume
            and int(_cpt.peerAvgVolume.replace(",", "")) > int(_cpt.clientVolume.replace(",", ""))
        ):
            potential_cpt_count += 1

            # Get the CPT code with the highest difference btn peerAvgVolume and clientVolume
            if not quick_win_top_code:
                quick_win_top_code = _cpt
                continue

            # Check if the current CPT code has a higher difference
            if (
                isinstance(_cpt.diffVolume, int | float)
                and isinstance(quick_win_top_code.diffVolume, int | float)
                and _cpt.diffVolume > quick_win_top_code.diffVolume
            ):
                quick_win_top_code = _cpt

    if potential_cpt_count:
        tags_list.append(Tag(text=f"{potential_cpt_count} Quick-Win Codes", color="green"))
    if quick_win_top_code:
        tags_list.append(Tag(text=f"{quick_win_top_code.code} - Top Gap", color="green"))
    return tags_list
