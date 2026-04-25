from __future__ import annotations

import asyncio
import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.geocoding import calculate_distance_miles
from app.types.common_provider_siteofcare import Location, Taxonomy
from app.types.cpt import CPT
from app.types.google_maps import GooglePlace


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


class Provider(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    npi: str | None
    name: str | None
    profilePicture: str | None = None
    taxonomy: Taxonomy = Taxonomy()
    location: Location = Location()
    affiliation: _Affiliation = _Affiliation()
    contact: _Contact = _Contact()
    licensure: list[str] = []
    # kpi: int | None = None

    latitude: float | None = None  # Not in Alphasophia output
    longitude: float | None = None  # Not in Alphasophia output
    distance_from_source_miles: float | None = None  # Not in Alphasophia output
    drive_time_minutes: float | None = None  # Drive time from source; set by generate_map()
    cpt_list: list[CPT] = []  # Not in Alphasophia output
    is_locum: bool = False  # Set after CPT profiles are fetched and totals are aggregated
    _cpt_fetched: bool = False  # Track if CPT profiles have been fetched
    nearest_google_place: GooglePlace | None = None
    distance_from_nearest_google_place_miles: float | None = (
        None  # Derived from nearest_google_place; set by stamp_nearest_google_place()
    )

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

        Raises ValueError if CPT profiles have not been fetched yet.
        """
        if not self._cpt_fetched:
            raise ValueError(
                f"Provider {self.id} (NPI: {self.npi}): CPT profiles must be fetched before calling set_is_locum"
            )
        self.is_locum = self.cpt_total_services <= 0.02 * share_volume

    def stamp_nearest_google_place(
        self, google_places: list[GooglePlace], distance_threshold_miles: float = 0.125
    ) -> None:
        nearest_place = None
        nearest_distance = float("inf")

        if self.latitude is None or self.longitude is None:
            logging.warning(
                f"Provider {self.id} (NPI: {self.npi}): Latitude or longitude is None; "
                "cannot calculate distance to Google Places"
            )
            return

        for place in google_places:
            if place.latitude is None or place.longitude is None:
                logging.warning(
                    f"Google Place '{place.name}' (ID: {place.place_id}): "
                    "Latitude or longitude is None; skipping distance calculation for this place"
                )
                continue
            dist = calculate_distance_miles(
                lat1=self.latitude,
                lon1=self.longitude,
                lat2=place.latitude,
                lon2=place.longitude,
            )
            if dist is not None and dist < nearest_distance and dist <= distance_threshold_miles:
                nearest_distance = dist
                nearest_place = place

        self.nearest_google_place = nearest_place
        self.distance_from_nearest_google_place_miles = nearest_distance
        return None

    @property
    def cpt_total_services(self) -> int:
        if self._cpt_fetched:
            return sum(cpt.totalServices for cpt in self.cpt_list)
        logging.warning(
            f"Provider {self.id} (NPI: {self.npi}): CPT profiles have not been fetched yet;"
            " returning 0 for cpt_total_services"
        )
        return 0
