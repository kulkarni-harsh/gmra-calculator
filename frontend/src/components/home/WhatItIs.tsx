interface Feature {
  num: string
  title: string
  body: string
}

const FEATURES: ReadonlyArray<Feature> = [
  {
    num: '01',
    title: 'Provider Volume in Your Market',
    body: 'See how many providers are already serving your specialty within your selected drive-time radius. Understand the competitive landscape before you commit.',
  },
  {
    num: '02',
    title: 'Procedure Activity for Your Specialty',
    body: 'Standard and custom reports include procedure-level market activity for the procedures most relevant to your specialty — so you can evaluate demand specific to what you actually do, not just general volume.',
  },
  {
    num: '03',
    title: 'Diagnosis Patterns by ICD-10 and DRG',
    body: 'Market-level diagnosis data shows whether the patient population in your target area reflects the clinical demand your specialty depends on.',
  },
  {
    num: '04',
    title: 'Any Specialty. Any Market.',
    body: 'Works for any outpatient specialty — new location, lease renewal, or practice expansion. Designed exclusively for independent physicians and non-hospital-owned groups of 1 to 50 providers.',
  },
]

export default function WhatItIs() {
  return (
    <section id="what-it-is" className="px-5 py-18 md:px-14 md:py-20">
      <div className="text-[10px] font-bold uppercase tracking-[4px] text-mcrec-teal">What It Is</div>
      <h2 className="mt-3 font-[family-name:var(--font-heading)] text-[clamp(28px,4vw,42px)] leading-tight tracking-[2px] text-mcrec-navy">
        The Starting Point for Every Lease{' '}
        <span className="text-mcrec-blue">Decision, Renewal, and Expansion</span>
      </h2>
      <hr className="mt-4 mb-6 h-[3px] w-[60px] border-0 bg-gradient-to-r from-mcrec-blue to-mcrec-teal" />
      <p className="max-w-[640px] text-sm leading-[1.8] text-mcrec-gray">
        Knowing the income-producing factors of a location is the starting point for every lease
        negotiation and every lease renewal. Without that data, you are negotiating blind. The
        Medical Real Estate Calculator™ changes that.
      </p>

      <div className="mt-7 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div
            key={f.num}
            className="rounded-sm border border-mcrec-light bg-white p-7 transition-colors hover:border-mcrec-blue"
          >
            <div className="font-[family-name:var(--font-heading)] text-4xl leading-none text-mcrec-light">
              {f.num}
            </div>
            <div className="mt-2 text-sm font-bold text-mcrec-navy">{f.title}</div>
            <div className="mt-2 text-xs leading-[1.7] text-mcrec-gray">{f.body}</div>
          </div>
        ))}
      </div>

      <div className="mt-7 rounded-sm border border-mcrec-light bg-white p-8">
        <h3 className="font-[family-name:var(--font-heading)] text-[22px] tracking-wide text-mcrec-navy">
          How the Data Works
        </h3>
        <p className="mt-2.5 text-xs leading-[1.8] text-mcrec-gray">
          Every report is built from publicly available market-level data — procedure activity,
          ICD-10 diagnosis patterns, and DRG information at the market level. We never request, use,
          or analyze individual patient records, proprietary billing files, or any protected health
          information. Your clinical data stays with your practice. The data we provide is market
          intelligence — not a review of anything inside your organization.
        </p>
        <p className="mt-3.5 text-[11px] font-semibold text-mcrec-teal">
          Powered by AlphaSophia · MCREC Reports LLC · Inspired by 25 Years of Globe Fiduciary Work
        </p>
      </div>
    </section>
  )
}
