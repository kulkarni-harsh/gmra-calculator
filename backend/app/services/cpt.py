import pandas as pd


def flag_anchor_cpt_codes(
    hospitals_within_range_df: pd.DataFrame,
    specialty_anchor_cpt_ranges: list[tuple[str, str]],
    specialty_anchor_individual_cpt_list: list[str],
) -> tuple[pd.DataFrame, int]:
    """Flag anchor CPT codes in the hospitals_within_range_df DataFrame and return DF & sum.

    Add columns to indicate whether each CPT code is an anchor code.

    Args
    ----
        hospitals_within_range_df (pd.DataFrame): DataFrame containing hospital data with CPT codes.
        specialty_anchor_cpt_ranges (list[tuple[str, str]]): List of tuples representing CPT code ranges.
        specialty_anchor_individual_cpt_list (list[str]): List of individual CPT codes.

    Returns
    -------
        pd.DataFrame: Updated DataFrame with anchor CPT code flags.
        int: Total count of anchor CPT visits across all hospitals.
    """
    anchor_visits_count = 0
    cpt_columns = [
        col
        for col in hospitals_within_range_df.columns
        if col.startswith("Procedure Volume") and col.split(":")[-1].strip().isalnum()
    ]
    for col in cpt_columns:
        _cpt_code = col.split(":")[-1].strip()
        _is_anchor = check_cpt_in_ranges(_cpt_code, specialty_anchor_cpt_ranges, specialty_anchor_individual_cpt_list)

        if _is_anchor:
            anchor_visits_count += hospitals_within_range_df[col].sum()

        hospitals_within_range_df[f"{col} - is_anchor"] = _is_anchor

    return hospitals_within_range_df, int(anchor_visits_count)


def get_top_cpt_df(hospitals_within_range_df: pd.DataFrame, cpt_lookup_df: pd.DataFrame) -> pd.DataFrame:
    """Get a DataFrame of the top CPT codes by volume along with their descriptions.

    Args
    ----
        hospitals_within_range_df (pd.DataFrame): DataFrame containing hospital data with CPT codes.
        cpt_lookup_df (pd.DataFrame): DataFrame containing CPT codes and their descriptions.

    Returns
    -------
        pd.DataFrame: DataFrame with columns for CPT code, count, and description, sorted by count in descending order.
    """
    cpt_columns = [
        col
        for col in hospitals_within_range_df.columns
        if col.startswith("Procedure Volume") and col.split(":")[-1].strip().isalnum()
    ]
    cpt_description_dict = dict(zip(cpt_lookup_df["HCPCS"], cpt_lookup_df["DESCRIPTION"], strict=True))

    top_cpt_df = hospitals_within_range_df[cpt_columns].sum().sort_values(ascending=False).reset_index()
    top_cpt_df.columns = ["cpt", "cpt_count"]
    top_cpt_df["cpt"] = top_cpt_df["cpt"].apply(lambda x: x.split(":")[-1].strip())
    top_cpt_df["cpt_description"] = top_cpt_df["cpt"].map(cpt_description_dict).fillna("N/A")
    # Convert cpt_count to integer
    top_cpt_df["cpt_count"] = top_cpt_df["cpt_count"].astype(int)

    return top_cpt_df


def generate_cpt_placeholders(top_cpt_df: pd.DataFrame) -> dict[str, str]:
    """Generate a dictionary of placeholders for the top CPT codes, their descriptions, and counts."""
    cpt_placeholder_dict = {}

    cpt_placeholder_dict.update({f"{{CPT_{i + 1}}}": value for i, value in enumerate(top_cpt_df["cpt"].values)})
    cpt_placeholder_dict.update(
        {f"{{CPT_{i + 1}_desc}}": value for i, value in enumerate(top_cpt_df["cpt_description"].values)}
    )
    cpt_placeholder_dict.update(
        {f"{{CPT_{i + 1}_count}}": f"{value:,}" for i, value in enumerate(top_cpt_df["cpt_count"].values)}
    )

    return cpt_placeholder_dict


def generate_hospitals_placeholders(
    hospitals_within_range_df: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """Generate a dictionary of placeholders for the top hospitals within range, their names, addresses, and distances.

     Create placeholders for 10 hospitals. If there are <10 hospitals, fill remaining placeholders with N/A.

     Placeholders include:
     - {sr_1}, {sr_2}, ..., {sr_10} for hospital rank
     - {prov_1_name}, {prov_2_name}, ..., {prov_10_name} for hospital names
     - {prov_1_address}, {prov_2_address}, ..., {prov_10_address} for hospital addresses
     - {prov_1_dis}, {prov_2_dis}, ..., {prov_10_dis} for hospital distances from source

     The function returns both the placeholder dictionary and the actual number of hospitals within range (up to 10).
    This allows the caller to know how many valid hospital entries are present when filling in the placeholders
    """
    filtered_hospitals_within_range_df = hospitals_within_range_df.head(10)
    hospitals_placeholder_dict: dict[str, int | str] = {}
    # Generate placeholders for up to 10 hospitals
    hospitals_placeholder_dict.update({f"{{sr_{i}}}": i for i in range(1, len(filtered_hospitals_within_range_df) + 1)})
    # Generate placeholders for hospital names and distances
    hospitals_placeholder_dict.update(
        {
            f"{{prov_{i}_name}}": name
            for i, name in enumerate(filtered_hospitals_within_range_df["Name"].values, start=1)
        }
    )

    hospitals_placeholder_dict.update(
        {
            f"{{prov_{i}_address}}": name
            for i, name in enumerate(
                filtered_hospitals_within_range_df["Primary Practice First Line"].values,
                start=1,
            )
        }
    )

    hospitals_placeholder_dict.update(
        {
            f"{{prov_{i}_dis}}": f"{dist:.1f}"
            for i, dist in enumerate(
                filtered_hospitals_within_range_df["distance_from_source_miles"].values,
                start=1,
            )
        }
    )
    # Fill in placeholders for hospitals less than 10 with N/A
    return hospitals_placeholder_dict, filtered_hospitals_within_range_df.shape[0]


def parse_anchor_codes_filters(
    codes_str: str,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Parse anchor codes filters from a string.

    Args
    ----
        codes_str (str): A string containing anchor codes filters, e.g., "99381-99397, G0438-G0439".

    Returns
    -------
        tuple[list[tuple[str, str]], list[str]]:
            A tuple containing a list of code ranges (as tuples) and a list of individual codes.
    """
    ranges: list[tuple[str, str]] = []
    individual_codes: list[str] = []
    for part in codes_str.split(","):
        part = part.strip().replace("–", "-")
        if part.isalnum():
            individual_codes.append(part)
        elif "-" in part:
            start, end = part.split("-")
            if start and end and start.isalnum() and end.isalnum():
                ranges.append((start.strip(), end.strip()))
            else:
                print(f"Unrecognized range format: {part}")
        else:
            print(f"Unrecognized code format: {part}")
    return ranges, individual_codes


def check_cpt_in_ranges(cpt: str, cpt_ranges: list[tuple[str, str]], individual_cpt_list: list[str]) -> bool:
    """Check if a CPT code falls within any of the specified ranges.

    Args
    ----
        cpt (str): The CPT code to check (in uppercase).
        cpt_ranges (list[tuple[str, str]]): A list of code ranges (as tuples).
        individual_cpt_list (list[str]): A list of individual CPT codes.

    Returns
    -------
        bool: True if the CPT code is within any range, False otherwise.
    """
    if cpt in individual_cpt_list:
        return True
    for start, end in cpt_ranges:
        if start <= cpt <= end:
            return True
    return False
