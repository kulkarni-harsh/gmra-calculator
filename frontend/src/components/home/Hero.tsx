import { Link } from 'react-router-dom'

const STATS: ReadonlyArray<{ num: React.ReactNode; label: string; sub?: string }> = [
  { num: <>25<span className="text-mcrec-blue">+</span></>, label: 'Years of Fiduciary' },
  { num: <span className="text-mcrec-blue">Any</span>, label: 'Specialty', sub: 'CPT · DRG · ICD-10' },
  { num: <><sup className="text-[20px] align-top">$</sup>399</>, label: 'Starting Price' },
  { num: <span className="text-mcrec-blue">Any</span>, label: 'U.S. Market' },
]

export default function Hero() {
  return (
    <header
      id="home"
      className="relative overflow-hidden bg-mcrec-navy px-5 pb-16 pt-18 md:px-14 md:pb-20 md:pt-20"
    >
      <div
        aria-hidden
        className="absolute right-0 top-0 h-full w-1/2 bg-[linear-gradient(135deg,rgba(43,108,176,0.08)_0%,transparent_70%)]"
      />

      <div className="relative">
        <div className="text-[10px] font-bold uppercase tracking-[4px] text-mcrec-teal">
          An Independent Market Intelligence Tool
        </div>

        <h1 className="mt-5 font-[family-name:var(--font-heading)] text-[clamp(48px,6vw,80px)] leading-[0.95] tracking-[3px] text-white">
          Clinical Demand.
          <span className="block">
            Precise <span className="text-mcrec-blue">Locations.</span>
          </span>
        </h1>

        <p className="mt-5 max-w-[640px] text-[15px] leading-[1.8] text-white/70">
          <strong className="font-semibold text-white">The Medical Real Estate Calculator™</strong>{' '}
          is a patent-pending market intelligence tool that uses CPT, DRG, and ICD-10 billing code
          data to analyze the income-producing factors of any medical office location in the United
          States. Before you sign a lease, renew one, or open a new facility — you need to know what
          the market actually supports for your specialty. The Calculator gives independently
          growing practices access to the same clinical demand intelligence hospital systems have
          used for years.
        </p>

        <p className="mt-3 max-w-[580px] text-[11px] leading-[1.7] text-white/40">
          Built for independent physicians and non-hospital-owned groups only. Not for hospital
          systems or large health networks. Built from market-level CPT, DRG, and ICD-10 data. Zero
          patient records. Zero PHI. Ever.
        </p>

        <div className="mt-9 grid max-w-[720px] grid-cols-2 gap-5 md:grid-cols-4">
          {STATS.map((s, i) => (
            <div key={i} className="text-center">
              <div className="font-[family-name:var(--font-heading)] text-[clamp(28px,4vw,44px)] leading-none tracking-wide text-white">
                {s.num}
              </div>
              <div className="mt-1 text-[9px] font-semibold uppercase tracking-[2px] text-mcrec-gray2">
                {s.label}
              </div>
              {s.sub && (
                <div className="mt-1.5 text-[10px] font-semibold tracking-[0.5px] text-mcrec-teal">
                  {s.sub}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-8 flex flex-wrap gap-3.5">
          <a
            href="#reports"
            className="inline-block rounded-sm bg-mcrec-blue px-7 py-3.5 text-xs font-bold uppercase tracking-wide text-white transition-all hover:-translate-y-px hover:bg-[#1E5A9A]"
          >
            View Reports &amp; Pricing
          </a>
          <a
            href="#what-it-is"
            className="inline-block rounded-sm border border-white/30 bg-transparent px-7 py-3.5 text-xs font-bold uppercase tracking-wide text-white transition-colors hover:border-white"
          >
            How It Works
          </a>
          <Link
            to="/buy"
            className="inline-block rounded-sm border border-mcrec-teal/40 bg-transparent px-7 py-3.5 text-xs font-bold uppercase tracking-wide text-mcrec-teal transition-colors hover:bg-mcrec-teal/10"
          >
            Start Order →
          </Link>
        </div>
      </div>
    </header>
  )
}
