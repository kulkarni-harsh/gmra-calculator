import pandas as pd
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.report_generator import (
    RawReportInput,
    _build_zip_stats_df,
    _providers_to_df,
    _sites_of_care_to_df,
)
from app.types.alphasophia import Provider
from app.types.cpt import CPT
from app.types.google_maps import SiteOfCare
from app.types.common_provider_siteofcare import Location, Taxonomy
from app.types.baseline_report_template import Upgrade


def _make_provider(npi="1111111111", lat=40.0, lon=-74.0, drive_time=10.0) -> Provider:
    p = Provider(
        id=1,
        npi=npi,
        name="Dr. Test",
        latitude=lat,
        longitude=lon,
        drive_time_minutes=drive_time,
        is_locum=False,
    )
    p.taxonomy = Taxonomy(description="Family Medicine")
    p._cpt_fetched = True
    p.cpt_list = [
        CPT(code="99213", totalServices=300, totalCharges=0.0, description="Office visit, est"),
        CPT(code="99214", totalServices=200, totalCharges=0.0, description="Office visit, est"),
    ]
    return p


def test_providers_to_df_columns():
    providers = [_make_provider()]
    df = _providers_to_df(providers, ["99213", "99214"])
    assert set(["npi", "name", "latitude", "longitude", "drive_time_minutes",
                "is_locum", "taxonomy_description", "cpt_total_services",
                "cpt_99213", "cpt_99214"]).issubset(df.columns)


def test_providers_to_df_values():
    providers = [_make_provider(npi="1111111111", lat=40.0, lon=-74.0, drive_time=10.0)]
    df = _providers_to_df(providers, ["99213", "99214"])
    assert df.iloc[0]["npi"] == "1111111111"
    assert df.iloc[0]["cpt_99213"] == 300
    assert df.iloc[0]["cpt_99214"] == 200
    assert df.iloc[0]["cpt_total_services"] == 500
    assert df.iloc[0]["is_locum"] is False


def test_providers_to_df_is_locum_threshold():
    p = _make_provider()
    p.cpt_list = [CPT(code="99213", totalServices=100, totalCharges=0.0)]
    df = _providers_to_df([p], ["99213"])
    assert df.iloc[0]["is_locum"] is True  # 100 <= 400


def test_sites_of_care_to_df_columns():
    soc = SiteOfCare(
        place_id="place_001",
        name="Clinic A",
        latitude=40.0,
        longitude=-74.0,
        drive_time_minutes=12.0,
        is_locum=False,
        npi_list=["111", "222"],
        cpt_list=[
            CPT(code="99213", totalServices=600, totalCharges=0.0),
            CPT(code="99214", totalServices=400, totalCharges=0.0),
        ],
    )
    soc.taxonomy = Taxonomy(description="Family Medicine")
    df = _sites_of_care_to_df([soc], ["99213", "99214"])
    assert set(["place_id", "name", "latitude", "longitude", "drive_time_minutes",
                "is_locum", "taxonomy_description", "npi_list",
                "cpt_total_services", "cpt_99213", "cpt_99214"]).issubset(df.columns)
    assert df.iloc[0]["cpt_total_services"] == 1000
    assert df.iloc[0]["npi_list"] == "111,222"


def test_build_zip_stats_df():
    actual_zips_df = pd.DataFrame({
        "zip": ["07001", "07002"],
        "lat": [40.0, 40.1],
        "lon": [-74.0, -74.1],
    })
    fracs = {"07001": 0.8, "07002": 0.5}
    pops = {"07001": 8000, "07002": 5000}
    df = _build_zip_stats_df(fracs, pops, actual_zips_df)
    assert set(["zip", "overlap_fraction", "scaled_population", "lat", "lon"]).issubset(df.columns)
    assert len(df) == 2
    assert df[df["zip"] == "07001"].iloc[0]["scaled_population"] == 8000
    assert df[df["zip"] == "07001"].iloc[0]["overlap_fraction"] == 0.8


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


from app.services.report_generator import _aggregate_cpt_data_from_df


def _make_peers_df() -> pd.DataFrame:
    return pd.DataFrame({
        "npi": ["111", "222"],
        "drive_time_minutes": [10.0, 20.0],
        "is_locum": [False, False],
        "taxonomy_description": ["Family Medicine", "Family Medicine"],
        "cpt_total_services": [500, 300],
        "cpt_99213": [300, 200],
        "cpt_99214": [200, 100],
    })


def test_aggregate_cpt_data_from_df_total_services():
    df = _make_peers_df()
    result = _aggregate_cpt_data_from_df(
        peers_df=df,
        cpt_codes=["99213", "99214"],
        cpt_patient_type_map={"99213": "Established", "99214": "Established"},
        cpt_descriptions={"99213": "Office visit, est", "99214": "Office visit, est"},
        provider_state="NJ",
        rvu_table={},
        gpci_table={},
    )
    assert result.total_market_services == 800  # (300+200) + (200+100)


def test_aggregate_cpt_data_from_df_share_denom():
    df = _make_peers_df()
    result = _aggregate_cpt_data_from_df(
        peers_df=df,
        cpt_codes=["99213", "99214"],
        cpt_patient_type_map={},
        cpt_descriptions={},
        provider_state="NJ",
        rvu_table={},
        gpci_table={},
    )
    assert result.share_denom == 800  # sum of cpt_total_services


def test_aggregate_cpt_data_from_df_cpt_rows_sorted():
    df = _make_peers_df()
    result = _aggregate_cpt_data_from_df(
        peers_df=df,
        cpt_codes=["99213", "99214"],
        cpt_patient_type_map={},
        cpt_descriptions={"99213": "Office visit, est"},
        provider_state="NJ",
        rvu_table={},
        gpci_table={},
    )
    # 99213 has volume 500, 99214 has volume 300 — 99213 must be first
    assert result.cpt_rows[0].code == "99213"
    assert result.cpt_rows[0].desc == "Office visit, est"


def test_aggregate_cpt_data_from_df_provider_shares():
    df = _make_peers_df()
    result = _aggregate_cpt_data_from_df(
        peers_df=df,
        cpt_codes=["99213", "99214"],
        cpt_patient_type_map={},
        cpt_descriptions={},
        provider_state="NJ",
        rvu_table={},
        gpci_table={},
    )
    # Two providers; shares should be sorted descending
    assert len(result.provider_shares) == 2
    assert result.provider_shares[0].share >= result.provider_shares[1].share


def test_aggregate_cpt_data_from_df_empty_df():
    df = pd.DataFrame(columns=["npi", "drive_time_minutes", "is_locum",
                                "taxonomy_description", "cpt_total_services",
                                "cpt_99213"])
    result = _aggregate_cpt_data_from_df(
        peers_df=df,
        cpt_codes=["99213"],
        cpt_patient_type_map={},
        cpt_descriptions={},
        provider_state="NJ",
        rvu_table={},
        gpci_table={},
    )
    assert result.total_market_services == 0
    assert result.share_denom == 1  # guard against divide-by-zero
    assert len(result.provider_shares) == 0


# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture
def minimal_raw() -> RawReportInput:
    return _minimal_raw()


# ── assemble_and_render_report tests ─────────────────────────────────────────

from app.services.report_generator import assemble_and_render_report


@pytest.mark.asyncio
async def test_assemble_and_render_report_returns_html(minimal_raw):
    with (
        patch("app.services.report_generator._generate_map_image", new_callable=AsyncMock) as mock_map,
        patch("app.services.report_generator.render_report", return_value="<html>TEST</html>") as mock_render,
    ):
        mock_map.return_value = (None, {}, [])
        html = await assemble_and_render_report(minimal_raw)
    assert html == "<html>TEST</html>"
    mock_render.assert_called_once()


@pytest.mark.asyncio
async def test_assemble_total_population_from_zip_stats(minimal_raw):
    """total_population must equal sum of scaled_population in zip_stats_df."""
    captured = {}

    def capture_render(tier, data):
        captured["data"] = data
        return "<html/>"

    with (
        patch("app.services.report_generator._generate_map_image", new_callable=AsyncMock) as mock_map,
        patch("app.services.report_generator.render_report", side_effect=capture_render),
    ):
        mock_map.return_value = (None, {}, [])
        await assemble_and_render_report(minimal_raw)

    # zip_stats_df has scaled_population=[8000] → total_population="8,000"
    assert captured["data"].totalPopulation == "8,000"


@pytest.mark.asyncio
async def test_assemble_active_providers_excludes_locum(minimal_raw):
    """activeProviders must count only non-locum rows in providers_df."""
    extra_row = pd.DataFrame({
        "npi": ["9999999999"],
        "name": ["Locum Dr."],
        "latitude": [40.1],
        "longitude": [-74.1],
        "drive_time_minutes": [25.0],
        "is_locum": [True],
        "taxonomy_description": ["Family Medicine"],
        "cpt_total_services": [100],
        "cpt_99213": [60],
        "cpt_99214": [40],
    })
    minimal_raw.providers_df = pd.concat(
        [minimal_raw.providers_df, extra_row], ignore_index=True
    )
    captured = {}

    def capture_render(tier, data):
        captured["data"] = data
        return "<html/>"

    with (
        patch("app.services.report_generator._generate_map_image", new_callable=AsyncMock) as mock_map,
        patch("app.services.report_generator.render_report", side_effect=capture_render),
    ):
        mock_map.return_value = (None, {}, [])
        await assemble_and_render_report(minimal_raw)

    assert captured["data"].activeProviders == 1
    assert captured["data"].locumCount == 1
