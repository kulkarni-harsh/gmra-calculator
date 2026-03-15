import { CheckCircle2 } from 'lucide-react'

const items = [
  'Comprehensive PDF Report',
  'Competitive Analysis vs. Local Providers',
  'Through-the-Door CPT Code Breakdown',
  'Revenue Benchmarks by Procedure',
  'Local Demographics & Population Analysis',
  'Provider Density Benchmark',
]

export default function Deliverables() {
  return (
    <section className="bg-[hsl(209_76%_95%)] px-6 py-20">
      <div className="mx-auto max-w-[1280px]">
        <div className="mb-10 text-center">
          <h2 className="font-[family-name:var(--font-heading)] text-4xl tracking-wide text-[hsl(215_63%_14%)] md:text-5xl">
            WHAT&apos;S INCLUDED IN YOUR REPORT
          </h2>
          <p className="mt-3 text-[hsl(215_20%_55%)]">
            Everything you need to make a confident, data-driven growth decision.
          </p>
        </div>

        <div className="mx-auto grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-2">
          {items.map((item) => (
            <div key={item} className="flex items-center gap-3 rounded-lg bg-white px-5 py-4 shadow-sm">
              <CheckCircle2 size={20} className="shrink-0 text-[hsl(149_64%_29%)]" />
              <span className="text-sm font-medium text-[hsl(215_63%_14%)]">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
