import { Link } from 'react-router-dom'

export default function CtaSection() {
  return (
    <section id="order" className="bg-mcrec-navy px-5 py-14 text-center md:px-14">
      <h2 className="font-[family-name:var(--font-heading)] text-[clamp(28px,4vw,42px)] leading-tight tracking-[2px] text-white">
        Order Your <span className="text-mcrec-blue">Report</span>
      </h2>
      <p className="mx-auto mt-3 max-w-[520px] text-[13px] leading-[1.8] text-white/60">
        Market data is the starting point for every lease decision. Order direct — any specialty,
        any market. No Globe Medical Realty Advisors engagement required. No brokerage relationship
        created. Use the data however you choose.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3.5">
        <Link
          to="/buy"
          className="inline-block rounded-sm bg-mcrec-blue px-7 py-3.5 text-xs font-bold uppercase tracking-wide text-white transition-all hover:-translate-y-px hover:bg-[#1E5A9A]"
        >
          Order a Report — Starting $399
        </Link>
        <a
          href="https://www.globemedllc.com"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block rounded-sm border border-white/30 px-7 py-3.5 text-xs font-bold uppercase tracking-wide text-white transition-colors hover:border-white"
        >
          Learn About Globe GMRA
        </a>
      </div>
      <div className="mt-5 text-xs text-mcrec-gray2">
        <a href="mailto:reports@medrecalc.com" className="text-mcrec-teal hover:underline">
          reports@medrecalc.com
        </a>{' '}
        ·{' '}
        <a href="tel:+18884772241" className="text-mcrec-teal hover:underline">
          1-888-477-2241
        </a>
        <br />
        <a
          href="https://www.medicalrealestatecalculator.com"
          className="text-white/40 hover:underline"
        >
          medicalrealestatecalculator.com
        </a>{' '}
        ·{' '}
        <a href="https://www.globemedllc.com" className="text-white/40 hover:underline">
          globemedllc.com
        </a>
      </div>
    </section>
  )
}
