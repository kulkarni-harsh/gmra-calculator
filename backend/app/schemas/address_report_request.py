# backend/app/schemas/address_report_request.py
from pydantic import BaseModel, EmailStr, Field, field_validator


class AddressReportRequest(BaseModel):
    specialty_name: str = Field(..., description="Specialty name (must match specialty_lookup)")
    address_line_1: str = Field(..., description="Street address line 1")
    address_line_2: str | None = Field(None, description="Suite / floor / unit (optional)")
    city: str = Field(..., description="City")
    state: str = Field(..., description="2-letter US state code")
    zip_code: str = Field(..., description="5-digit ZIP code")
    drive_time_minutes: int = Field(
        ...,
        description="Drive-time catchment in minutes. Must be one of: 10, 30, 45, 60.",
    )
    customer_email: EmailStr = Field(..., description="Email to send the finished report to")
    payment_intent_id: str = Field(..., description="Stripe PaymentIntent ID — verified before job enqueue")

    @field_validator("customer_email")
    @classmethod
    def validate_customer_email(cls, value: str) -> str:  # noqa: N805
        if str(value).lower().strip() not in [
            "david@gm-ra.com",
            "harsh.kulkarni.42774@gmail.com",
            "harshsk17@gmail.com",
            "d.rutson@gmail.com",
        ]:
            raise ValueError("Ineligible Customer Email")
        return value

    @field_validator("drive_time_minutes")
    @classmethod
    def validate_drive_time_minutes(cls, value: int) -> int:  # noqa: N805
        if value not in {10, 30, 45, 60}:
            raise ValueError("drive_time_minutes must be one of: 10, 30, 45, 60")
        return value
