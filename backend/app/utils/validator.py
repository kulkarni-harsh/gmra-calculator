import pandas as pd


def validate_speciality_master_df(df: pd.DataFrame) -> None:
    """Validate the structure and content of the specialty master DataFrame."""
    required_columns = [
        "Male",
        "Female",
        "0-4",
        "5-9",
        "10-14",
        "15-17",
        "18-19",
        "20",
        "21",
        "22-24",
        "25-29",
        "30-34",
        "35-39",
        "40-44",
        "45-49",
        "50-54",
        "55-59",
        "60-61",
        "62-64",
        "65-66",
        "67-69",
        "70-74",
        "75-79",
        "80-84",
        "85-1000",
    ]
    for col in required_columns:
        if col not in df.columns:
            print("Error: Missing required column", col)
            raise ValueError(f"Missing required column: {col}")
        if set(df[col].unique()).difference({"Y", "N"}):
            print("Warning: Column", col, "contains values other than 'Y' and 'N'")
    print("Specialty Master DataFrame validation completed.")


def validate_geocoding_inputs(
    input_address_line_1: str,
    input_city: str,
    input_state: str,
    input_zip_code: str,
    input_providers_df: pd.DataFrame,
) -> bool:
    """Validates the inputs for geocoding.

    Args
    ----
    input_address_line_1 (str): The first line of the address to be geocoded.
    input_city (str): The city of the address to be geocoded.
    input_state (str): The state of the address to be geocoded.
    input_zip_code (str): The zip code of the address to be geocoded.
    input_providers_df (pd.DataFrame): The DataFrame containing provider information.

    Returns
    -------
    bool: True if the inputs are valid, otherwise raises a ValueError with an appropriate message
    """
    if any(pd.isnull(x) for x in [input_address_line_1, input_city, input_state, input_zip_code]):
        raise ValueError("Please provide a complete address for geocoding.")
    if not isinstance(input_providers_df, pd.DataFrame) or input_providers_df.empty:
        raise ValueError("Input providers DataFrame is empty.")
    input_providers_df = input_providers_df.rename(
        columns={
            "Primary Practice Address Line 1": "Primary Practice First Line",
            "Primary Practice Address Line 2": "Primary Practice Second Line",
        }
    )
    reqd_cols = [
        "Name",
        "Primary Practice First Line",
        "Primary Practice Second Line",
        "Primary Practice City",
        "Primary Practice ZIP",
        "Primary Practice State",
    ]
    if set(reqd_cols).difference(set(input_providers_df.columns)):
        raise ValueError(
            f"Input providers excel is missing {set(reqd_cols).difference(set(input_providers_df.columns))}"
            " columns. \n\n"
            "Ensure to have the following columns: " + ", ".join([f"'{_}'" for _ in reqd_cols])
        )
    return True
