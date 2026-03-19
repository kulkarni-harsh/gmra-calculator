from pydantic import BaseModel, EmailStr, Field

from app.types.alphasophia import Provider


class CreatePaymentIntentRequest(BaseModel):
    customer_email: EmailStr
    provider_name: str
    specialty_name: str
    client_provider: Provider
    miles_radius: int


class CreateT0PaymentIntentRequest(BaseModel):
    customer_email: EmailStr
    specialty_name: str
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state: str
    zip_code: str
    miles_radius: int = Field(..., ge=1, le=100)
