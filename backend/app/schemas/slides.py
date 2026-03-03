from pydantic import BaseModel, Field


class GenerateSlidesRequest(BaseModel):
    address_line_1: str = Field(..., description="The first line of the provider's address")
    address_line_2: str = Field(None, description="The second line of the provider's address (optional)")
    city: str = Field(..., description="The city where the provider is located")
    state: str = Field(..., description="The state where the provider is located")
    zip_code: str = Field(..., description="The ZIP code of the provider's location")
    specialty_name: str = Field(..., description="The medical specialty of the provider")
    miles_radius: int = Field(..., description="The radius in miles for the provider's service area")

    