import pandas as pd

from .cpt import parse_anchor_codes_filters


def get_specialty_population(
    hospitals_within_range_df: pd.DataFrame,
    specialty_master_df: pd.DataFrame,
    specialty_name: str,
    locality_demographics_dict: dict,
) -> tuple[str, int, float | None, float | None, bool | None]:
    """
    Calculate specialty-specific population and provider metrics.

    Args:
    hospitals_within_range_df (pd.DataFrame): DataFrame of hospitals within the specified range.
    specialty_master_df (pd.DataFrame): DataFrame containing specialty master data.
    specialty_name (str): The name of the specialty to analyze.
    locality_demographics_dict (dict): Dictionary containing demographic information for the locality.

    Returns:
    tuple[str, int, float, float, bool | None]: A tuple containing the specialty demographic type, total population,
    target average providers per 100k, current average providers per 100k, and a boolean indicating if the current
    supply is less than the target supply.
    """
    specialty_name = specialty_name.strip().lower()

    if "Specialty" not in specialty_master_df.columns:
        raise ValueError("Error: 'Specialty' column not found in specialty master sheet.")

    if specialty_name not in specialty_master_df["Specialty"].apply(lambda x: str(x).strip().lower()).values:
        print(f"Warning: Specialty '{specialty_name}' not found in specialty master sheet.")
        print(f"Defaulting to entire population for specialty '{specialty_name}'.")
        return "N/A", locality_demographics_dict["Total"], None, None, None

    specialty_row = specialty_master_df[
        specialty_master_df["Specialty"].astype(str).str.strip().str.lower() == specialty_name
    ].iloc[0]

    is_male = specialty_row["Male"] == "Y"
    is_female = specialty_row["Female"] == "Y"
    target_demographic_type = specialty_row["Typical Patient Range"]
    target_avg_provider_per_100k = float(specialty_row["Avg Physicians per 100k"])
    current_num_providers = hospitals_within_range_df.shape[0]

    total_population = 0
    for age_group in locality_demographics_dict["M"].keys():
        if age_group == "Total":
            continue

        include_age_group = specialty_row.get(age_group, "N") == "Y"
        if include_age_group:
            if is_male:
                total_population += locality_demographics_dict["M"][age_group]
            if is_female:
                total_population += locality_demographics_dict["F"][age_group]

    current_avg_provider_per_100k = (current_num_providers / total_population) * 100000 if total_population > 0 else 0

    return (
        target_demographic_type,
        total_population,
        target_avg_provider_per_100k,
        current_avg_provider_per_100k,
        current_avg_provider_per_100k < target_avg_provider_per_100k,
    )


def get_specialty_anchor_cpt_info(
    specialty_master_df: pd.DataFrame,
    specialty_name: str,
) -> tuple[tuple[list[tuple[str, str]], list[str]], int]:
    """
    Retrieve anchor CPT code ranges and individual CPT codes for a given specialty.

    Args
    ----
        specialty_master_df (pd.DataFrame): DataFrame containing specialty master data.
        specialty_name (str): The name of the specialty to analyze.

    Returns
    -------
        tuple[tuple[list[tuple[str, str]], list[str]], int]: A tuple containing a tuple of
        (CPT code ranges, individual CPT codes) and the target anchor visits count.

    """
    specialty_name = specialty_name.strip().lower()

    if (
        "Specialty" not in specialty_master_df.columns
        or "Anchor CPT Codes" not in specialty_master_df.columns
        or "Target Anchor Visits" not in specialty_master_df.columns
    ):
        raise ValueError(
            "Error: 'Specialty' or 'Anchor CPT Codes' or 'Target Anchor Visits'"
            " column not found in specialty master sheet."
        )

    if specialty_name not in specialty_master_df["Specialty"].apply(lambda x: str(x).strip().lower()).values:
        print(f"Warning: Specialty '{specialty_name}' not found in specialty master sheet.")
        return parse_anchor_codes_filters("99202-99215, 99381-99397, G0438-G0439"), 4200

    specialty_row = specialty_master_df[
        specialty_master_df["Specialty"].astype(str).str.strip().str.lower() == specialty_name
    ].iloc[0]
    return parse_anchor_codes_filters(specialty_row["Anchor CPT Codes"]), specialty_row["Target Anchor Visits"]
