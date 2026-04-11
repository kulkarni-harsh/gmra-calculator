# app/schemas/t2_report_request.py
from pydantic import Field, field_validator

from app.schemas.address_report_request import AddressReportRequest


class T2ReportRequest(AddressReportRequest):
    cpt_codes: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="1–5 CPT codes to analyze (overrides specialty defaults)",
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
