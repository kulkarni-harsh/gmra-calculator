from pydantic import BaseModel, Field

from app.types.alphasophia import Provider


class ProviderRequest(BaseModel):
    # Input should be specialty name, client hcp ID (selected from dropdown), miles radius
    specialty_name: str = Field(..., description="The name of the provider's specialty")
    client_provider: Provider = Field(..., description="The client provider for client vs market comparison")
    miles_radius: int = Field(..., description="The radius in miles to search for providers")
