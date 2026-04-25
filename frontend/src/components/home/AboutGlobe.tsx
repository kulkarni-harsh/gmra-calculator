import type { ComponentType, SVGProps } from 'react'
import { ChartColumnIncreasing, Database, Scale, ShieldCheck } from 'lucide-react'

interface Card {
  icon: ComponentType<SVGProps<SVGSVGElement>>
  title: string
  body: string
}

const CARDS: ReadonlyArray<Card> = [
  {
    icon: Scale,
    title: 'Fiduciary Standard — Always',
    body: "Globe never represents landlords, hospitals, or developers. Every engagement is physician-side with a legal obligation to the physician's outcome.",
  },
  {
    icon: ChartColumnIncreasing,
    title: 'Data-First for 25 Years',
    body: "Clinical demand analysis has been Globe's first step in every client engagement — before location, before negotiation, before recommendation.",
  },
  {
    icon: ShieldCheck,
    title: 'Zero Patient Data — Ever',
    body: 'Every report uses publicly available market-level data only. No PHI. No EHR access. No billing records requested from your practice.',
  },
  {
    icon: Database,
    title: 'Powered by AlphaSophia',
    body: 'Our data partner provides access to hundreds of millions of market-level procedure records for procedure activity, ICD-10, and DRG analysis at any geography.',
  },
]

export default function AboutGlobe() {
  return (
    <section className="px-5 py-18 md:px-14 md:py-20">
      <div className="text-[10px] font-bold uppercase tracking-[4px] text-mcrec-teal">
        About Globe Medical Realty Advisors
      </div>
      <h2 className="mt-3 font-[family-name:var(--font-heading)] text-[clamp(28px,4vw,42px)] leading-tight tracking-[2px] text-mcrec-navy">
        25 Years. Fiduciary for{' '}
        <span className="text-mcrec-blue">Independent Physicians.</span>
      </h2>
      <hr className="mt-4 mb-6 h-[3px] w-[60px] border-0 bg-gradient-to-r from-mcrec-blue to-mcrec-teal" />
      <p className="max-w-[640px] text-sm leading-[1.8] text-mcrec-gray">
        Globe Medical Realty Advisors has spent 25 years representing independent physicians and
        non-hospital-owned medical groups — exclusively. Globe has never represented a hospital or a
        landlord. Every engagement is physician-side, fiduciary standard, nationally.
      </p>

      <div className="mt-7 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {CARDS.map((c) => (
          <div key={c.title} className="p-6 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-mcrec-blue/8 text-mcrec-blue ring-1 ring-mcrec-blue/12">
              <c.icon className="h-7 w-7 stroke-[1.8]" aria-hidden="true" />
            </div>
            <h4 className="mt-3 text-[15px] font-bold tracking-[0.3px] text-mcrec-navy md:text-[17px]">
              {c.title}
            </h4>
            <p className="mt-1.5 text-xs leading-[1.6] text-mcrec-gray">{c.body}</p>
          </div>
        ))}
      </div>

      <div className="mt-7 text-center">
        <p className="mb-1 text-sm font-bold text-mcrec-navy">
          Never a Hospital. Never a Landlord. Always Physician-Side.
        </p>
        <a
          href="https://www.globemedllc.com"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-block rounded-sm border border-mcrec-blue px-7 py-3.5 text-xs font-bold uppercase tracking-wide text-mcrec-blue hover:bg-mcrec-blue hover:text-white"
        >
          Visit Globe Medical Realty Advisors →
        </a>
      </div>
    </section>
  )
}
