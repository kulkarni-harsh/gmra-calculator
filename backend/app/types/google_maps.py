"""Google Places + Site-of-Care domain models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.types.common_provider_siteofcare import Location, Taxonomy
from app.types.cpt import CPT


class GooglePlace(BaseModel):
    """A single Google Places result (or our own derived 'place')."""

    model_config = ConfigDict(extra="allow")

    place_id: str
    name: str | None = None
    vicinity: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None


class SiteOfCare(GooglePlace):
    """A site of care — one or more providers grouped by Google `place_id`.

    Locum providers (no Google place match) get a synthetic place_id of
    `locum_<npi>` so they remain individually addressable.
    """

    model_config = ConfigDict(extra="allow")

    taxonomy: Taxonomy = Taxonomy()
    location: Location = Location()
    is_locum: bool
    distance_from_source_miles: float | None = None  # filled by report generator
    drive_time_minutes: float | None = None  # filled by mapbox.generate_map()
    cpt_list: list[CPT] = []  # aggregated CPT volumes from all providers at this place
    npi_list: list[str] = []  # NPIs of providers attached to this place

    @property
    def cpt_total_services(self) -> int:
        """Total of `totalServices` across every CPT in `cpt_list`."""
        return sum(cpt.totalServices for cpt in self.cpt_list)

    def get_cpt_profile(self, cpt_code: str) -> CPT | None:
        """Return the `CPT` row matching `cpt_code`, or `None` if absent."""
        return next((cpt for cpt in self.cpt_list if cpt.code == cpt_code), None)
