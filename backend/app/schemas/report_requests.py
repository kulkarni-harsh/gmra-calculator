# backend/app/schemas/report_requests.py
from typing import ClassVar

from pydantic import BaseModel, EmailStr, Field, field_validator


class T1ReportRequest(BaseModel):
    specialty_name: str = Field(..., description="Specialty name (must match specialty_lookup)")
    address_line_1: str = Field(..., description="Street address line 1")
    address_line_2: str | None = Field(None, description="Suite / floor / unit (optional)")
    city: str = Field(..., description="City")
    state: str = Field(..., description="2-letter US state code")
    zip_code: str = Field(..., description="5-digit ZIP code")
    drive_time_minutes: int = Field(
        ...,
        description="Drive-time catchment in minutes. Must be one of: 5, 10, 15, 30, 45, 60.",
    )
    customer_email: EmailStr = Field(..., description="Email to send the finished report to")
    payment_intent_id: str = Field(..., description="Stripe PaymentIntent ID — verified before job enqueue")

    tier_name: ClassVar[str] = "Market Entry Report"
    tier_description: ClassVar[str] = (
        "Comprehensive market entry report with through the door CPT code analysis, "
        "and actionable insights to help you understand the competitive landscape and "
        "identify growth opportunities in your target market."
    )

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
        if value not in {5, 10, 15, 30, 45, 60}:
            raise ValueError("drive_time_minutes must be one of: 5, 10, 15, 30, 45, 60")
        return value


class T2ReportRequest(T1ReportRequest):
    cpt_codes: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="1-5 CPT codes to analyze (overrides specialty defaults)",
    )

    tier_name: ClassVar[str] = "Current Market Analysis"
    tier_description: ClassVar[str] = (
        "Focused market analysis with through the door CPT code and up to 1-5 additional CPT codes, "
        "to help you understand the competitive landscape and identify growth opportunities in your target market."
    )

    @field_validator("cpt_codes")
    @classmethod
    def validate_cpt_codes(cls, value: list[str]) -> list[str]:  # noqa: N805
        if not (1 <= len(value) <= 5):
            raise ValueError("cpt_codes must contain between 1 and 5 codes")
        cleaned = [c.strip() for c in value]
        for code in cleaned:
            if not code:
                raise ValueError("CPT code cannot be blank")
        return cleaned


class T3ReportRequest(T1ReportRequest):
    cpt_codes: list[str] = Field(
        ...,
        min_length=1,
        max_length=15,
        description="1-15 CPT codes to analyze (overrides specialty defaults)",
    )

    tier_name: ClassVar[str] = "In-depth Market Analysis"
    tier_description: ClassVar[str] = (
        "In-depth market analysis with through the door CPT code and up to 1-15 additional CPT codes, "
        "to help you understand the competitive landscape and identify growth opportunities in your target market."
        "Includes additional gaps analysis to help you identify areas for improvement."
    )

    @field_validator("cpt_codes")
    @classmethod
    def validate_cpt_codes(cls, value: list[str]) -> list[str]:  # noqa: N805
        if not (1 <= len(value) <= 15):
            raise ValueError("cpt_codes must contain between 1 and 15 codes")
        cleaned = [c.strip() for c in value]
        for code in cleaned:
            if not code:
                raise ValueError("CPT code cannot be blank")
        return cleaned
