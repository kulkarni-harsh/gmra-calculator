"""All common types related to both Provider and SiteOfCare"""

from pydantic import BaseModel, ConfigDict


class Taxonomy(BaseModel):
    model_config = ConfigDict(extra="allow")
    code: str | None = None
    description: str | None = None
    count: int | None = None


class Location(BaseModel):
    model_config = ConfigDict(extra="allow")
    address_line_1: str | None = None  # Not in Alphasophia output
    address_line_2: str | None = None  # Not in Alphasophia output
    zip_code: str | None = None  # Not in Alphasophia output
    city: str | None = None
    state: str | None = None
