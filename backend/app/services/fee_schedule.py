"""Medicare Physician Fee Schedule calculator (CY 2026).

Formula (CMS):
  Non-Facility payment = (Work_RVU × PW_GPCI + NonFac_PE_RVU × PE_GPCI + MP_RVU × MP_GPCI) × CF
  Facility   payment = (Work_RVU × PW_GPCI + Fac_PE_RVU   × PE_GPCI + MP_RVU × MP_GPCI) × CF

Why QPP (not nonQPP):
  The anchor CPT codes are standard physician office/outpatient E&M and preventive visit
  codes (99202-99215, AWV, etc.) billed under the Medicare Physician Fee Schedule (PFS)
  and eligible for the Quality Payment Program. nonQPP covers facility-only codes,
  anesthesia (ANES2026.csv), and procedures excluded from the value-based payment modifier.

Usage (app.state pattern):
  # In lifespan (main.py):
  app.state.rvu_table, app.state.gpci_table = load_fee_schedule_tables()

  # In a request handler:
  rate = get_medicare_rate("99213", "CA", request.app.state.rvu_table, request.app.state.gpci_table)
"""

from __future__ import annotations

import logging

# load_fee_schedule_tables is imported here so callers only need this module.
from app.utils.common import load_fee_schedule_tables as load_fee_schedule_tables  # noqa: F401


def get_medicare_rate(
    cpt_code: str,
    state: str,
    rvu_table: dict[str, dict],
    gpci_table: dict[str, dict],
    *,
    facility: bool = False,
) -> float | None:
    """Return the Medicare allowed amount for one unit of a CPT code in a state.

    Args:
        cpt_code:   HCPCS/CPT code string (e.g. "99213").
        state:      Two-letter state abbreviation (e.g. "CA").
        rvu_table:  Preloaded RVU table from app.state.rvu_table.
        gpci_table: Preloaded GPCI table from app.state.gpci_table.
        facility:   If True, use Facility PE RVU (hospital/ASC); otherwise
                    use Non-Facility PE RVU (office setting).

    Returns:
        Dollar amount rounded to 2 decimal places, or None if the code or
        state is not found in the fee schedule.
    """
    rvu = rvu_table.get(cpt_code.strip())
    if rvu is None:
        logging.debug("CPT code %s not found in RVU table", cpt_code)
        return None

    state_key = state.strip().upper()
    gpci = gpci_table.get(state_key)
    if gpci is None:
        logging.debug("State %s not found in GPCI table; using national (1.0) GPCIs", state_key)
        gpci = {"pw": 1.0, "pe": 1.0, "mp": 1.0}

    pe_rvu = rvu["pe_fac"] if facility else rvu["pe_nonfac"]
    payment = (rvu["work"] * gpci["pw"] + pe_rvu * gpci["pe"] + rvu["mp"] * gpci["mp"]) * rvu["cf"]
    return round(payment, 2)
