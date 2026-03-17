from pydantic import BaseModel, Field

from app.types.alphasophia import Provider
from pydantic import field_validator

class ProviderRequest(BaseModel):
    # Input should be specialty name, client hcp ID (selected from dropdown), miles radius
    specialty_name: str = Field(..., description="The name of the provider's specialty")
    client_provider: Provider = Field(..., description="The client provider for client vs market comparison")
    miles_radius: int = Field(..., description="The radius in miles to search for providers")
    customer_email: str = Field(..., description="Email address to send the finished report to")

    @field_validator("customer_email")
    def validate_customer_email(cls, value: str):
        if str(value).lower().strip() not in [
            "david@gm-ra.com",
            "harsh.kulkarni.42774@gmail.com",
            "harshsk17@gmail.com"
        ]:
            raise ValueError("Ineligible Customer Email")
        return value
