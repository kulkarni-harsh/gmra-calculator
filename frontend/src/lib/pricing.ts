/**
 * Single source of truth for tier display prices on the frontend.
 * Keep in sync with the backend cent constants in app/services/payment.py.
 *   T1_REPORT_AMOUNT_CENTS = 39_900  → $399
 *   T2_REPORT_AMOUNT_CENTS = 49_900  → $499
 *   T3_REPORT_AMOUNT_CENTS = 59_900  → $599
 *   T4_REPORT_AMOUNT_CENTS = 99_900  → $999
 */
export const TIER_PRICES = {
  0: '$399',  // T1  Market Entry Report
  1: '$499',  // T2  Current Market Analysis
  2: '$599',  // T3  In-depth Market Analysis
  3: '$999',  // T4  Custom Market Expansion Report
} as const satisfies Record<0 | 1 | 2 | 3, string>
