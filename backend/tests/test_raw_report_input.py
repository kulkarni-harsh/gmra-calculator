import pandas as pd

from app.services.report_generator import RawReportInput
from app.types.baseline_report_template import Upgrade


def _minimal_raw() -> RawReportInput:
    providers_df = pd.DataFrame({
        "npi": ["1234567890"],
        "name": ["Dr. Smith"],
        "latitude": [40.0],
        "longitude": [-74.0],
        "drive_time_minutes": [15.0],
        "is_locum": [False],
        "taxonomy_description": ["Family Medicine"],
        "cpt_total_services": [500],
        "cpt_99213": [300],
        "cpt_99214": [200],
    })
    zip_stats_df = pd.DataFrame({
        "zip": ["07001"],
        "overlap_fraction": [0.8],
        "scaled_population": [8000],
        "lat": [40.0],
        "lon": [-74.0],
    })
    return RawReportInput(
        report_id="TEST-001",
        specialty_name="Family Medicine",
        city="Newark",
        state="NJ",
        zip_code="07001",
        address_line_1="123 Main St",
        address_line_2=None,
        drive_time_minutes=30,
        tier_name="Market Entry Report",
        show_section03=False,
        source_lat=40.0,
        source_lon=-74.0,
        use_site_of_care=False,
        cpt_codes=["99213", "99214"],
        cpt_patient_type_map={"99213": "Established", "99214": "Established"},
        cpt_descriptions={"99213": "Office visit, est", "99214": "Office visit, est"},
        taxonomy_codes=["207Q00000X"],
        source_tabs=["Family Medicine"],
        density_scope="State",
        target_density_per_100k=95.0,
        rvu_table={},
        gpci_table={},
        providers_df=providers_df,
        sites_of_care_df=None,
        zip_stats_df=zip_stats_df,
        combined_demo={"M": {}, "F": {}, "Total": 10000},
        analysis_text="Market analysis text.",
        upgrades=[Upgrade(price="$999", name="Strategic Report", desc="Full analysis")],
    )


def test_raw_report_input_instantiates():
    raw = _minimal_raw()
    assert raw.report_id == "TEST-001"
    assert raw.specialty_name == "Family Medicine"
    assert len(raw.providers_df) == 1
    assert len(raw.zip_stats_df) == 1
