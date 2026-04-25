"""Unit tests for app.utils.validator."""

import logging

import pandas as pd
import pytest

from app.utils.validator import (
    validate_geocoding_inputs,
    validate_speciality_master_df,
)

_AGE_COLS = [
    "Male", "Female",
    "0-4", "5-9", "10-14", "15-17", "18-19", "20", "21", "22-24",
    "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
    "60-61", "62-64", "65-66", "67-69", "70-74", "75-79", "80-84", "85-1000",
]


def _make_specialty_df(values: str = "Y") -> pd.DataFrame:
    return pd.DataFrame({col: [values, values] for col in _AGE_COLS})


def test_validate_speciality_master_df_passes_with_y_n():
    df = _make_specialty_df("Y")
    df["50-54"] = ["N", "Y"]
    validate_speciality_master_df(df)  # no exception


def test_validate_speciality_master_df_raises_on_missing_column():
    df = _make_specialty_df()
    df = df.drop(columns=["Male"])
    with pytest.raises(ValueError, match="Missing required column: Male"):
        validate_speciality_master_df(df)


def test_validate_speciality_master_df_warns_on_invalid_values(caplog):
    """Non-Y/N values should log a warning but not raise."""
    df = _make_specialty_df()
    df["10-14"] = ["X", "Y"]
    with caplog.at_level(logging.WARNING):
        validate_speciality_master_df(df)
    assert any("10-14" in rec.message for rec in caplog.records)


# ── validate_geocoding_inputs ─────────────────────────────────────────────────


def _make_provider_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Name": ["Dr A"],
            "Primary Practice First Line": ["123 Main St"],
            "Primary Practice Second Line": [""],
            "Primary Practice City": ["Austin"],
            "Primary Practice ZIP": ["78701"],
            "Primary Practice State": ["TX"],
        }
    )


def test_validate_geocoding_inputs_returns_true_on_valid():
    df = _make_provider_df()
    assert validate_geocoding_inputs("123 Main St", "Austin", "TX", "78701", df) is True


def test_validate_geocoding_inputs_raises_on_null_address():
    df = _make_provider_df()
    with pytest.raises(ValueError, match="complete address"):
        validate_geocoding_inputs(None, "Austin", "TX", "78701", df)


def test_validate_geocoding_inputs_raises_on_empty_df():
    with pytest.raises(ValueError, match="empty"):
        validate_geocoding_inputs("123 Main St", "Austin", "TX", "78701", pd.DataFrame())


def test_validate_geocoding_inputs_raises_on_missing_columns():
    df = pd.DataFrame({"Name": ["Dr A"]})
    with pytest.raises(ValueError, match="missing"):
        validate_geocoding_inputs("123 Main St", "Austin", "TX", "78701", df)
