from pydantic import BaseModel, EmailStr, Field, field_validator

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
        description="Drive-time catchment in minutes. Must be one of: 10, 30, 45, 60.",
    )
    @field_validator("drive_time_minutes")
    @classmethod
    def validate_drive_time_minutes(cls, value: int) -> int:  # noqa: N805
        if value not in {10, 30, 45, 60}:
            raise ValueError("drive_time_minutes must be one of: 10, 30, 45, 60")
        return value
