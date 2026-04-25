interface UseCase {
  num: string
  title: string
  body: string
  tag: string
}

const STATS: ReadonlyArray<{ value: string; label: string; sub: string }> = [
  { value: '5–15', label: 'Year Lease Commitment', sub: 'Every decision locks in for years' },
  { value: '#2', label: 'P&L Line Item', sub: 'Rent is second only to staffing' },
  { value: '2026', label: 'Decision Year', sub: 'Old market data no longer applies' },
  { value: '$399', label: 'Starting Price', sub: 'vs. $10K+ for a consultant' },
]

const USE_CASES: ReadonlyArray<UseCase> = [
  {
    num: '01',
    title: 'Physicians Leaving Hospital Systems',
    body: "When hospital employment no longer makes financial sense, physicians entering the independent market for the first time need to know which markets support their specialty before they sign their first independent lease. That decision used to require hiring a consultant. Now it starts with a $399 report. We have seen this scenario play out for 25 years — and the physicians who have market data before they negotiate always get better outcomes than those who don't.",
    tag: 'New Independence',
  },
  {
    num: '02',
    title: 'Practices in the Last 18 Months of Their Lease',
    body: 'Any independently operating practice whose lease expires in 2026 or 2027 is making a renewal or relocation decision in the middle of the largest reimbursement shift in years. Market data from three years ago may no longer reflect what your location can actually support — or what a new one could. The income-producing factors of your current location may have fundamentally changed. A $399 report answers that question before you sit down at the negotiating table.',
    tag: 'Renewal / Relocation',
  },
  {
    num: '03',
    title: 'Groups Evaluating New or Expanded Facilities',
    body: 'As site neutrality changes the competitive dynamics of hospital outpatient departments in your market, capacity may be opening for independent practices. Markets that were previously saturated by hospital-affiliated locations may now have room for independent providers. Understanding whether a market supports expansion before you invest in it is exactly what this tool was built for.',
    tag: 'Expansion',
  },
]

export default function SiteNeutrality() {
  return (
    <section id="site-neutrality" className="bg-mcrec-navy px-5 py-20 md:px-14">
      <div className="text-[10px] font-bold uppercase tracking-[4px] text-mcrec-gold">
        2026 · Site Neutrality · The One Big Beautiful Bill
      </div>
      <h2 className="mt-3 font-[family-name:var(--font-heading)] text-[clamp(32px,5vw,52px)] leading-tight tracking-[2px] text-white">
        The Largest Wave of Independent Practice{' '}
        <span className="text-mcrec-gold">Decisions</span> in a Generation
      </h2>
      <hr className="mt-4 mb-6 h-[3px] w-[80px] border-0 bg-gradient-to-r from-mcrec-gold to-mcrec-teal" />

      <div className="mb-10 max-w-[720px] space-y-4 text-[15px] leading-[1.9] text-white/75">
        <p>
          Site neutrality provisions in the One Big Beautiful Bill reduce the reimbursement
          advantage hospital outpatient departments have historically held over independent office
          settings. For decades, that advantage has driven physician employment decisions, real
          estate strategies, and market consolidation. When that advantage shrinks — or disappears —
          the calculus changes for everyone.
        </p>
        <p>
          For independently growing practices, this is the most significant shift in medical real
          estate economics since the ACA. Location decisions made in 2026 and 2027 will play out
          over 5- to 15-year lease terms. Making those decisions with outdated market data — or no
          market data at all — is the single most expensive mistake a practice can make right now.
        </p>
      </div>

      <div className="mb-11 grid gap-5 sm:grid-cols-2 md:grid-cols-4">
        {STATS.map((s) => (
          <div
            key={s.label}
            className="rounded-sm border border-mcrec-gold/20 bg-mcrec-gold/[0.08] p-6 text-center"
          >
            <div className="font-[family-name:var(--font-heading)] text-[42px] leading-none text-mcrec-gold">
              {s.value}
            </div>
            <div className="mt-1 text-[10px] font-semibold uppercase tracking-[2px] text-white/50">
              {s.label}
            </div>
            <div className="mt-1.5 text-[11px] text-white/40">{s.sub}</div>
          </div>
        ))}
      </div>

      <h3 className="mb-5 font-[family-name:var(--font-heading)] text-[26px] tracking-wide text-white">
        Who This Affects — and Why Market Data Matters Now
      </h3>
      <div className="grid gap-5 md:grid-cols-3">
        {USE_CASES.map((c) => (
          <div
            key={c.num}
            className="rounded-sm border border-white/10 bg-white/[0.06] p-7"
          >
            <div className="font-[family-name:var(--font-heading)] text-[32px] leading-none text-mcrec-gold">
              {c.num}
            </div>
            <div className="mt-2 text-[15px] font-bold text-white">{c.title}</div>
            <p className="mt-2.5 text-xs leading-[1.8] text-white/60">{c.body}</p>
            <span className="mt-3 inline-block rounded-sm border border-mcrec-gold/25 bg-mcrec-gold/10 px-2 py-1 text-[8px] font-bold uppercase tracking-[1.5px] text-mcrec-gold">
              {c.tag}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-9 flex flex-wrap items-center gap-7 rounded-sm border border-mcrec-gold/20 bg-mcrec-gold/[0.08] p-7">
        <div className="min-w-[280px] flex-1 space-y-3 text-sm leading-[1.8] text-white/75">
          <p>
            <strong className="text-white">
              Real estate is the second highest line item on a physician practice P&amp;L.
            </strong>{' '}
            Unlike staffing, it is locked in for 5 to 15 years. Hospital systems have had dedicated
            teams analyzing every market before every decision — using exactly the kind of clinical
            demand data this calculator provides. Independently growing practices have historically
            had to sign whatever the landlord put in front of them.
          </p>
          <p>
            <strong className="text-white">
              That is the problem this tool exists to solve — and 2026 has made it more urgent than
              ever.
            </strong>{' '}
            We have been doing this analysis for our clients for over 25 years. We understand what
            site neutrality means for your real estate decision because we have seen the data shift
            in real time. The question is not whether to get market data before your next lease
            decision. The question is whether you can afford not to.
          </p>
        </div>
        <div className="shrink-0">
          <a
            href="#reports"
            className="inline-block whitespace-nowrap rounded-sm bg-mcrec-blue px-7 py-3.5 text-xs font-bold uppercase tracking-wide text-white hover:bg-[#1E5A9A]"
          >
            Order a Report →
          </a>
          <a
            href="tel:+18884772241"
            className="mt-2.5 block text-center text-[11px] text-mcrec-gold"
          >
            1-888-477-2241
          </a>
        </div>
      </div>
    </section>
  )
}
