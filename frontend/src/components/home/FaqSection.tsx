import { useState } from 'react'

interface Faq {
  q: string
  a: string
}

const FAQS: ReadonlyArray<Faq> = [
  {
    q: 'Do I need to work with Globe to order a report?',
    a: 'No. The Medical Real Estate Calculator is an independent product operated by MCREC Reports LLC. You can order any report directly with no Globe engagement, no broker contact, and no obligation of any kind. Order the report, receive your data, use it however you choose.',
  },
  {
    q: 'What is site neutrality and why does it matter for my real estate decision?',
    a: 'Site neutrality provisions reduce the reimbursement premium that hospital outpatient departments have historically received versus independent office settings. When that premium shrinks, the financial logic of hospital employment changes — and so does the competitive landscape for independent practices. If you are making a real estate decision in 2026, the market data you had three years ago may no longer reflect what your location can support.',
  },
  {
    q: 'What data sources are used in the reports?',
    a: "All reports are built from publicly available market-level data including Medicare procedure activity, ICD-10 diagnosis patterns, DRG data, and NPI provider information. Data is sourced through AlphaSophia, MCREC Reports LLC's data partner. No patient records, no PHI, and no information from inside your practice is ever used.",
  },
  {
    q: 'What is the difference between the three report tiers?',
    a: 'Market Baseline ($399) gives you a full market-level picture of provider density and demand for your specialty. Practice-Specific ($499) adds 5 procedure categories tailored to your specialty for deeper analysis. Advanced Practice ($599) includes 15 procedure categories and is the most complete market picture available — it is also the report Globe fiduciary clients receive at no cost as part of their engagement.',
  },
  {
    q: "Can I use this report in my lease negotiation even if I don't have a broker?",
    a: 'Yes. The report is yours to use however you choose. Many physicians use it as an objective data foundation for lease negotiations, whether they are represented by a broker, negotiating directly, or simply evaluating whether to renew at all.',
  },
  {
    q: 'Is this tool appropriate for a physician group leaving a hospital system?',
    a: 'Yes — this is one of the most valuable use cases for the calculator. Before committing to your first independent lease, you need to know what the market supports for your specialty. The Market Baseline or Practice-Specific report gives you that foundation. If you decide later that you also want fiduciary tenant representation, Globe Medical Realty Advisors is available — but it is never required.',
  },
  {
    q: 'What does "income-producing factors" mean?',
    a: "Income-producing factors are the market-level data points that determine whether a location can support your specialty — including the volume of diagnoses your specialty treats in that market, the procedure activity already occurring, the number of competing providers, and the patient population's clinical demand profile. Real estate drives revenue only if the market can support your clinical volume.",
  },
  {
    q: 'Who operates the Medical Real Estate Calculator?',
    a: 'Reports are operated and delivered by MCREC Reports LLC, which holds the data agreement with AlphaSophia. The underlying patent and intellectual property are owned by MCREC LLC, which is the managing partner for the reports business. Globe Medical Realty Advisors is a separate fiduciary brokerage firm. Ordering a report creates a relationship with MCREC Reports LLC only — not with Globe.',
  },
]

export default function FaqSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  return (
    <section id="faq" className="bg-mcrec-off px-5 py-18 md:px-14 md:py-20">
      <div className="text-[10px] font-bold uppercase tracking-[4px] text-mcrec-teal">FAQs</div>
      <h2 className="mt-3 font-[family-name:var(--font-heading)] text-[clamp(28px,4vw,42px)] leading-tight tracking-[2px] text-mcrec-navy">
        Frequently Asked <span className="text-mcrec-blue">Questions</span>
      </h2>
      <hr className="mt-4 mb-6 h-[3px] w-[60px] border-0 bg-gradient-to-r from-mcrec-blue to-mcrec-teal" />

      <div className="mt-7 max-w-[720px]">
        {FAQS.map((f, i) => {
          const open = openIndex === i
          const buttonId = `faq-trigger-${i}`
          const panelId = `faq-panel-${i}`
          return (
            <div key={f.q} className="border-b border-mcrec-light">
              <button
                id={buttonId}
                type="button"
                onClick={() => setOpenIndex(open ? null : i)}
                className="relative w-full py-4.5 pr-10 text-left text-[13px] font-semibold leading-[1.5] text-mcrec-navy"
                aria-expanded={open}
                aria-controls={panelId}
              >
                {f.q}
                <span className="absolute right-0 top-1/2 -translate-y-1/2 text-lg font-light text-mcrec-blue">
                  {open ? '−' : '+'}
                </span>
              </button>
              <div
                id={panelId}
                role="region"
                aria-labelledby={buttonId}
                className={`grid overflow-hidden transition-[grid-template-rows] duration-300 ${
                  open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
                }`}
              >
                <div className="min-h-0">
                  <p className="pb-4.5 text-xs leading-[1.8] text-mcrec-gray">{f.a}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
