from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class CPT(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str | None
    codeType: str | None = None
    description: str | None = None
    sourceType: str | None = None
    dataset: Any | None = None
    totalServices: int = 0
    totalCharges: float = 0.0
    totalPatients: int = 0

    @field_validator("totalServices", mode="before")
    def convert_total_services(cls, value: Any) -> int:  # noqa: N805
        if value is not None:
            return int(value)
        logging.critical(f"totalServices is not an integer: {value}")
        return -1

    @field_validator("totalCharges", mode="before")
    def convert_total_charges(cls, value: Any) -> float:  # noqa: N805
        if value is not None:
            return float(value)
        return -0.1

    @field_validator("totalPatients", mode="before")
    def convert_total_patients(cls, value: Any) -> int:  # noqa: N805
        if value is not None:
            return int(value)
        logging.critical(f"totalPatients is not an integer: {value}")
        return -1

    def __add__(self, other: CPT) -> CPT:
        if not isinstance(other, CPT):
            return NotImplemented
        if self.code != other.code:
            raise ValueError(f"Cannot add CPT codes with different codes: {self.code} vs {other.code}")
        return CPT(
            code=self.code,
            codeType=self.codeType or other.codeType,
            description=self.description or other.description,
            sourceType=self.sourceType or other.sourceType,
            dataset=self.dataset or other.dataset,
            totalServices=self.totalServices + other.totalServices,
            totalCharges=self.totalCharges + other.totalCharges,
            totalPatients=self.totalPatients + other.totalPatients,
        )

    @staticmethod
    def merge_lists(list1: list[CPT], list2: list[CPT]) -> list[CPT]:
        """
        Merges two CPT lists. Same code -> totals are added via CPT.__add__.
        Codes unique to either list are kept as-is.
        """
        grouped: dict[str, CPT] = {}

        for cpt in list1 + list2:
            if cpt.code is None:
                continue
            if cpt.code in grouped:
                grouped[cpt.code] = grouped[cpt.code] + cpt
            else:
                grouped[cpt.code] = cpt

        return list(grouped.values())
