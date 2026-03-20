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
    drive_time_minutes: int = Field(
        ...,
        description="Drive-time catchment in minutes: 10 | 30 | 45 | 60",
    )
