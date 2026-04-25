from pydantic import BaseModel, EmailStr, Field, field_validator

from app.types.alphasophia import Provider


class CreatePaymentIntentRequest(BaseModel):
    customer_email: EmailStr
    provider_name: str
    specialty_name: str
    client_provider: Provider
    miles_radius: int


class CreateT1PaymentIntentRequest(BaseModel):
    """Market Entry Report payment intent request."""

    customer_email: EmailStr
    specialty_name: str
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state: str
    zip_code: str
    drive_time_minutes: int = Field(
        ...,
        description="Drive-time catchment in minutes. Must be one of: 5, 10, 15, 30, 45, 60.",
    )

    @field_validator("drive_time_minutes")
    @classmethod
    def validate_drive_time_minutes(cls, value: int) -> int:  # noqa: N805
        if value not in {5, 10, 15, 30, 45, 60}:
            raise ValueError("drive_time_minutes must be one of: 5, 10, 15, 30, 45, 60")
        return value


class CreateT2PaymentIntentRequest(BaseModel):
    """Same as T1 request, but with atmost 5 CPT codes."""

    customer_email: EmailStr
    specialty_name: str
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state: str
    zip_code: str
    drive_time_minutes: int = Field(
        ...,
        description="Drive-time catchment in minutes. Must be one of: 5, 10, 15, 30, 45, 60.",
    )
    cpt_codes: list[str] = Field(..., min_length=1, max_length=5)

    @field_validator("drive_time_minutes")
    @classmethod
    def validate_drive_time_minutes(cls, value: int) -> int:  # noqa: N805
        if value not in {5, 10, 15, 30, 45, 60}:
            raise ValueError("drive_time_minutes must be one of: 5, 10, 15, 30, 45, 60")
        return value

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


class CreateT3PaymentIntentRequest(BaseModel):
    """Same as Tier 2 with higher CPT code limit (atmost 15) and price. Used for the In-depth Market Analysis."""

    customer_email: EmailStr
    specialty_name: str
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state: str
    zip_code: str
    drive_time_minutes: int = Field(
        ...,
        description="Drive-time catchment in minutes. Must be one of: 5, 10, 15, 30, 45, 60.",
    )
    cpt_codes: list[str] = Field(..., min_length=1, max_length=15)

    @field_validator("drive_time_minutes")
    @classmethod
    def validate_drive_time_minutes(cls, value: int) -> int:  # noqa: N805
        if value not in {5, 10, 15, 30, 45, 60}:
            raise ValueError("drive_time_minutes must be one of: 5, 10, 15, 30, 45, 60")
        return value

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
