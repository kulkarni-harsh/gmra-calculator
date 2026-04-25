from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict

from app.types.common_provider_siteofcare import Location, Taxonomy
from app.types.cpt import CPT


class GooglePlace(BaseModel):
    """Site of Care Model"""

    model_config = ConfigDict(extra="allow")

    place_id: str
    name: str | None = None
    vicinity: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    


class SiteOfCare(GooglePlace):
    """Site of Care Model"""

    model_config = ConfigDict(extra="allow")
    # Inherits all fields from GooglePlace; can add more if needed in the future
    taxonomy: Taxonomy = Taxonomy()
    location: Location = Location()

    is_locum: bool
    distance_from_source_miles: float | None = None  # Derived from Provider lat/long
    drive_time_minutes: float | None = None  # Drive time from source; set by generate_map()
    cpt_list: list[
        CPT
    ] = []  # Derived from aggregated CPT data of all providers associated with this site; set during report generation
    
    npi_list: list[str] = []  # List of NPIs of providers associated with this site; set during report generation

    @property
    def cpt_total_services(self) -> int:
        return sum(cpt.totalServices for cpt in self.cpt_list)

    def get_cpt_profile(self, cpt_code: str) -> CPT | None:
        return next((cpt for cpt in self.cpt_list if cpt.code == cpt_code), None)
