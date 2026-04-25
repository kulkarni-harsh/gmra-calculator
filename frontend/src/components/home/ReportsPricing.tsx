import { Link } from 'react-router-dom'
import { TIER_PRICES } from '@/lib/pricing'

interface Tier {
  id: string
  tier: string
  name: string
  price: string
  desc: string
  features: ReadonlyArray<string>
  cta: string
  featured?: boolean
}

// TIER_PRICES values look like "$399"; strip the leading $ for the styled price chip.
const priceFor = (tierIndex: 0 | 1 | 2): string => TIER_PRICES[tierIndex].replace('$', '')

const TIERS: ReadonlyArray<Tier> = [
  {
    id: 'tier1',
    tier: 'Tier 1',
    name: 'Market Baseline',
    price: priceFor(0),
    desc: 'Best for physicians evaluating a market for the first time or wanting an objective read on provider density and market activity.',
    features: [
      'Provider volume in your drive-time market',
      'Market-level specialty activity',
      'Procedure, diagnosis & DRG market data',
      'Drive-time radius: 5, 10, 20, 30, or 45 min',
      'Any outpatient specialty',
    ],
    cta: 'Order Market Baseline →',
  },
  {
    id: 'tier2',
    tier: 'Tier 2',
    name: 'Practice-Specific',
    price: priceFor(1),
    desc: 'Ideal for lease renewals and new location decisions where demand for your specific procedures matters most.',
    features: [
      'Everything in Market Baseline',
      '5 procedure categories specific to your specialty',
      'Procedure-level market activity by category',
      'Drive-time radius: your choice',
      'Any outpatient specialty',
    ],
    cta: 'Order Practice-Specific →',
    featured: true,
  },
  {
    id: 'tier3',
    tier: 'Tier 3',
    name: 'Advanced Practice',
    price: priceFor(2),
    desc: 'For multi-provider groups and significant lease decisions requiring the most complete market picture available.',
    features: [
      'Everything in Practice-Specific',
      '15 procedure categories specific to your specialty',
      'Additional selections tailored to your needs',
      'Drive-time radius: your choice',
      'Globe fiduciary clients receive this tier at no cost',
    ],
    cta: 'Order Advanced Practice →',
  },
]

export default function ReportsPricing() {
  return (
    <section id="reports" className="px-5 py-18 md:px-14 md:py-20">
      <div className="text-[10px] font-bold uppercase tracking-[4px] text-mcrec-teal">
        Reports &amp; Pricing
      </div>
      <h2 className="mt-3 font-[family-name:var(--font-heading)] text-[clamp(28px,4vw,42px)] leading-tight tracking-[2px] text-mcrec-navy">
        Market Intelligence for <span className="text-mcrec-blue">Your Specialty</span>
      </h2>
      <hr className="mt-4 mb-6 h-[3px] w-[60px] border-0 bg-gradient-to-r from-mcrec-blue to-mcrec-teal" />
      <p className="max-w-[640px] text-sm leading-[1.8] text-mcrec-gray">
        Three tiers of clinical demand analysis. Every report covers your selected drive-time radius
        and is delivered as a complete market intelligence package.
      </p>

      <div className="mt-7 grid gap-5 md:grid-cols-3">
        {TIERS.map((t) => (
          <div
            key={t.id}
            className={`relative flex flex-col rounded-sm border bg-white p-8 transition-colors ${
              t.featured
                ? 'border-mcrec-blue ring-1 ring-mcrec-blue'
                : 'border-mcrec-light hover:border-mcrec-blue'
            }`}
          >
            {t.featured && (
              <span className="absolute left-1/2 top-[-10px] -translate-x-1/2 rounded-sm bg-mcrec-blue px-3 py-1 text-[8px] font-bold uppercase tracking-[2px] text-white">
                Most Popular
              </span>
            )}
            <div className="text-[10px] font-bold uppercase tracking-[3px] text-mcrec-teal">
              {t.tier}
            </div>
            <div className="mt-2 font-[family-name:var(--font-heading)] text-[26px] tracking-wide text-mcrec-navy">
              {t.name}
            </div>
            <div className="mt-1 font-[family-name:var(--font-heading)] text-[48px] leading-none text-mcrec-blue">
              <sup className="mr-0.5 align-top text-[20px]">$</sup>
              {t.price}
            </div>
            <p className="mt-2 text-xs leading-[1.6] text-mcrec-gray">{t.desc}</p>
            <ul className="my-5 flex-1 space-y-1.5 text-xs text-mcrec-gray">
              {t.features.map((f) => (
                <li key={f} className="relative pl-5 leading-[1.5]">
                  <span className="absolute left-0 top-0 text-[11px] font-bold text-mcrec-green">
                    ✓
                  </span>
                  {f}
                </li>
              ))}
            </ul>
            <div className="mt-auto text-center">
              <Link
                to="/buy"
                className={`inline-block rounded-sm px-7 py-3.5 text-xs font-bold uppercase tracking-wide transition-all ${
                  t.featured
                    ? 'bg-mcrec-blue text-white hover:-translate-y-px hover:bg-[#1E5A9A]'
                    : 'border border-mcrec-blue text-mcrec-blue hover:bg-mcrec-blue hover:text-white'
                }`}
              >
                {t.cta}
              </Link>
            </div>
          </div>
        ))}
      </div>

      <p className="mt-7 text-center text-[10px] leading-[1.6] text-mcrec-gray2">
        All reports are delivered as market intelligence by MCREC Reports LLC. No Globe Medical
        Realty Advisors engagement, brokerage relationship, or follow-up obligation of any kind is
        created by ordering a report. Zero patient data. Zero PHI. Ever.
      </p>
    </section>
  )
}
