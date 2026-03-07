from pydantic import BaseModel, Field

class ProviderRequest(BaseModel):
    address_line_1: str = Field(..., description="The first line of the provider's address")
    address_line_2: str = Field(..., description="The second line of the provider's address")
    city: str = Field(..., description="The city where the provider is located")
    state: str = Field(..., description="The state where the provider is located")
    zip_code: str = Field(..., description="The zip code of the provider's address")
    specialty_name: str = Field(..., description="The name of the provider's specialty")
    miles_radius: int = Field(..., description="The radius in miles to search for providers")