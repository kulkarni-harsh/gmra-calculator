from functools import lru_cache

import pandas as pd
import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.types import SexAgeCounts, ZipPopulationMap

_CENSUS_TIMEOUT = (10, 30)  # (connect, read)


def get_age_mapping(start_idx: int) -> dict[str, str]:
    """
    Get the mapping of census variable codes to age groups for either
    male or female demographics.

    The start_idx parameter determines whether the mapping is for
    male (start_idx=2) or female (start_idx=26) demographics.

    The mapping is based on the ACS 5-year estimates for the B01001
    table, which provides detailed age and sex breakdowns.
    """
    return {
        f"B01001_{start_idx:03d}E": "Total",
        f"B01001_{start_idx + 1:03d}E": "0-4",
        f"B01001_{start_idx + 2:03d}E": "5-9",
        f"B01001_{start_idx + 3:03d}E": "10-14",
        f"B01001_{start_idx + 4:03d}E": "15-17",
        f"B01001_{start_idx + 5:03d}E": "18-19",
        f"B01001_{start_idx + 6:03d}E": "20",
        f"B01001_{start_idx + 7:03d}E": "21",
        f"B01001_{start_idx + 8:03d}E": "22-24",
        f"B01001_{start_idx + 9:03d}E": "25-29",
        f"B01001_{start_idx + 10:03d}E": "30-34",
        f"B01001_{start_idx + 11:03d}E": "35-39",
        f"B01001_{start_idx + 12:03d}E": "40-44",
        f"B01001_{start_idx + 13:03d}E": "45-49",
        f"B01001_{start_idx + 14:03d}E": "50-54",
        f"B01001_{start_idx + 15:03d}E": "55-59",
        f"B01001_{start_idx + 16:03d}E": "60-61",
        f"B01001_{start_idx + 17:03d}E": "62-64",
        f"B01001_{start_idx + 18:03d}E": "65-66",
        f"B01001_{start_idx + 19:03d}E": "67-69",
        f"B01001_{start_idx + 20:03d}E": "70-74",
        f"B01001_{start_idx + 21:03d}E": "75-79",
        f"B01001_{start_idx + 22:03d}E": "80-84",
        f"B01001_{start_idx + 23:03d}E": "85-1000",
    }


@retry(
    retry=retry_if_exception_type(requests.exceptions.Timeout),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _fetch_zip_demographics(zip_codes_list: tuple[str, ...], api_key: str) -> list[list[str]]:
    male_vars = get_age_mapping(2)
    female_vars = get_age_mapping(26)
    vars_to_get = list(male_vars.keys()) + list(female_vars.keys()) + ["B01003_001E"]  # Total population

    params = {
        "get": ",".join(vars_to_get),
        "for": f"zip code tabulation area:{','.join(zip_codes_list)}",
        "key": api_key,
    }
    r = requests.get("https://api.census.gov/data/2022/acs/acs5", params=params, timeout=_CENSUS_TIMEOUT)
    r.raise_for_status()
    return r.json()


@lru_cache(maxsize=1000)
def get_zip_demographics(zip_codes_list: tuple[str], api_key: str) -> ZipPopulationMap:
    """
    Get demographic data for a list of zip codes from the US Census API.

    The function retrieves total population and age group breakdowns for both
    male and female demographics.

    Args
    ----
    zip_codes_list : tuple[str]
        A tuple of zip codes for which to retrieve demographic data.
    api_key : str
        A valid API key for accessing the US Census API.

    Returns
    -------
    dict[str, dict[str, dict[str, int]]]
        A dictionary where each key is a zip code and the value is another dictionary containing demographic data.
    """
    male_vars = get_age_mapping(2)
    female_vars = get_age_mapping(26)

    data = _fetch_zip_demographics(zip_codes_list, api_key)

    pop_df = pd.DataFrame(data[1:], columns=data[0])
    dict_data: ZipPopulationMap = (
        pop_df.set_index("zip code tabulation area")
        .apply(
            lambda row: {
                "M": {y: int(row[x]) for x, y in male_vars.items()},
                "F": {y: int(row[x]) for x, y in female_vars.items()},
                "Total": int(row["B01003_001E"]),
            },
            axis=1,
        )
        .to_dict()
    )
    return dict_data


def combine_demographics(pop1: SexAgeCounts, pop2: SexAgeCounts) -> SexAgeCounts:
    """Combine two demographic dictionaries by summing the counts for each age group and total population."""
    combined: SexAgeCounts = {"M": {}, "F": {}, "Total": pop1["Total"] + pop2["Total"]}

    for age_group in pop1["M"].keys():
        combined["M"][age_group] = pop1["M"][age_group] + pop2["M"][age_group]
        combined["F"][age_group] = pop1["F"][age_group] + pop2["F"][age_group]

    return combined
