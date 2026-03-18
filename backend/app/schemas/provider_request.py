from pydantic import BaseModel, EmailStr, Field, field_validator

from app.types.alphasophia import Provider


class ProviderRequest(BaseModel):
    specialty_name: str = Field(..., description="The name of the provider's specialty")
    client_provider: Provider = Field(..., description="The client provider for client vs market comparison")
    miles_radius: int = Field(..., description="The radius in miles to search for providers")
    customer_email: EmailStr = Field(..., description="Email address to send the finished report to")
    payment_intent_id: str = Field(..., description="Stripe PaymentIntent ID — verified before job enqueue")

    @field_validator("customer_email")
    def validate_customer_email(cls, value: str):  # noqa: N805
        if str(value).lower().strip() not in [
            "david@gm-ra.com",
            "harsh.kulkarni.42774@gmail.com",
            "harshsk17@gmail.com",
            "d.rutson@gmail.com",
        ]:
            raise ValueError("Ineligible Customer Email")
        return value
