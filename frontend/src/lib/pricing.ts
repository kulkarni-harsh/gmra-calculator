/**
 * Single source of truth for tier display prices on the frontend.
 * To change a price, update it here — TierSelection, Buy, and StepPayment
 * all derive their display strings from this map.
 *
 * Keep in sync with the backend cent constants in app/services/payment.py.
 */
export const TIER_PRICES = {
  0: '$399',  // T1  Market Entry Report
  1: '$599',  // T2  Through-the-Door Codes Report
  2: '$599',  // Coming Soon — 5-Code Strategic Report
  3: '$799',  // Coming Soon — 10-Code Full Analysis + Add-On
} as const satisfies Record<0 | 1 | 2 | 3, string>
