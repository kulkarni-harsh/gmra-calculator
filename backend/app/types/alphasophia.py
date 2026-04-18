from __future__ import annotations

import asyncio
import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, PrivateAttr, field_validator


class _Taxonomy(BaseModel):
    model_config = ConfigDict(extra="allow")
    code: str | None = None
    description: str | None = None
    count: int | None = None


class _Location(BaseModel):
    model_config = ConfigDict(extra="allow")
    address_line_1: str | None = None  # Not in Alphasophia output
    address_line_2: str | None = None  # Not in Alphasophia output
    zip_code: str | None = None  # Not in Alphasophia output
    city: str | None = None
    state: str | None = None


class _Affiliation(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str | None = None
    count: int | None = None
    is_sole_proprietor: bool | None = None


class _Contact(BaseModel):
    model_config = ConfigDict(extra="allow")
    email: list[str | None] | None = None
    phone: list[str | None] | None = None
    linkedin: list[str | None] | None = None
    twitter: list[str | None] | None = None
    doximity: list[str | None] | None = None


class CPT(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str | None
    codeType: str | None = None
    description: str | None = None
    sourceType: str | None = None
    dataset: Any | None = None
    totalServices: int = 0
    totalCharges: float = 0.0
    totalPatients: int = 0

    @field_validator("totalServices", mode="before")
    def convert_total_services(cls, value: Any) -> int:  # noqa: N805
        if value is not None:
            return int(value)
        logging.critical(f"totalServices is not an integer: {value}")
        return -1

    @field_validator("totalCharges", mode="before")
    def convert_total_charges(cls, value: Any) -> float:  # noqa: N805
        if value is not None:
            return float(value)
        # logging.critical(f"totalCharges is not a float: {value}")
        return -0.1

    @field_validator("totalPatients", mode="before")
    def convert_total_patients(cls, value: Any) -> int:  # noqa: N805
        if value is not None:
            return int(value)
        logging.critical(f"totalPatients is not an integer: {value}")
        return -1


class Provider(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    npi: str | None
    name: str | None
    profilePicture: str | None = None
    taxonomy: _Taxonomy = _Taxonomy()
    location: _Location = _Location()
    affiliation: _Affiliation = _Affiliation()
    contact: _Contact = _Contact()
    licensure: list[str] = []
    # kpi: int | None = None

    latitude: float | None = None  # Not in Alphasophia output
    longitude: float | None = None  # Not in Alphasophia output
    distance_from_source_miles: float | None = None  # Not in Alphasophia output
    drive_time_minutes: float | None = None  # Drive time from source; set by generate_map()
    cpt_list: list[CPT] = []  # Not in Alphasophia output
    cpt_total_services: int = 0  # Sum of totalServices across report CPT codes; set during report generation
    is_locum: bool | None = None  # Set after CPT profiles are fetched and totals are aggregated
    _cpt_fetched: bool = PrivateAttr(default=False)

    @field_validator("id", mode="before")
    def convert_to_int(cls, value: Any) -> int:  # noqa: N805
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            return int(value)
        logging.critical(f"HCP ID is not an integer: {value}")
        return -1

    async def update_address_and_zip(self):
        """Update address and zip code from NPI Registry API

        Args:
            npi (str): NPI number
        """
        from app.services.alphasophia import get_npi_address

        add1, add2, postal_code = await get_npi_address(self.npi)
        (self.location.address_line_1, self.location.address_line_2, self.location.zip_code) = (
            add1,
            add2,
            postal_code[:5] if isinstance(postal_code, str) else None,
        )

    async def update_lat_long(self):
        """Update latitude and longitude from Mapbox API"""
        from app.services.mapbox import get_location_coordinates

        lat, long = get_location_coordinates(
            f"{self.location.address_line_1}, {self.location.address_line_2}, "
            f"{self.location.city}, {self.location.state}"
        )
        self.latitude, self.longitude = lat, long

    async def fetch_cpt_profiles(self, cpt_codes: list[str]):
        """Fetch CPT profiles from Alphasophia API"""
        from app.services.alphasophia import get_hcp_procedure

        cpt_tasks = [get_hcp_procedure(hcp_id=self.id, page=1, code=cpt_code) for cpt_code in cpt_codes]
        gathered_results = await asyncio.gather(*cpt_tasks)
        self.cpt_list = [cpt for cpt_list in gathered_results for cpt in cpt_list]
        self._cpt_fetched = True

    def get_cpt_profile(self, cpt_code: str):
        return next((cpt for cpt in self.cpt_list if cpt.code == cpt_code), None)

    def set_is_locum(self, share_volume: int) -> None:
        """Mark provider as locum if their CPT volume is ≤ 2% of the total shared volume.

        share_volume is the sum of cpt_total_services across all in-radius providers
        (i.e. share_denom from _aggregate_cpt_data). Must be called AFTER both:
        1. fetch_cpt_profiles() — sets _cpt_fetched and populates cpt_list
        2. cpt_total_services has been summed externally (done by _aggregate_cpt_data)

        Raises ValueError if CPT profiles have not been fetched yet.
        """
        if not self._cpt_fetched:
            raise ValueError(
                f"Provider {self.id} (NPI: {self.npi}): CPT profiles must be fetched before calling set_is_locum"
            )
        self.is_locum = self.cpt_total_services <= 0.02 * share_volume
