import { BarChart3, Stethoscope, Users, Lightbulb } from 'lucide-react'

const pillars = [
  {
    icon: BarChart3,
    title: 'Competitive Benchmarking',
    body: 'See exactly how your practice stacks up against every provider within your chosen radius. Know where you lead — and where you can capture share.',
  },
  {
    icon: Stethoscope,
    title: 'Procedure & Revenue Insights',
    body: 'Identify which CPT codes drive the most revenue in your market, backed by real Medicare fee schedule data and local utilization patterns.',
  },
  {
    icon: Users,
    title: 'Local Demographics Analysis',
    body: 'Understand the patient population in your market — age breakdowns, sex distribution, and total relevant population for your specialty.',
  },
  {
    icon: Lightbulb,
    title: 'Actionable Strategy',
    body: 'Every report includes a complimentary 1-on-1 strategy call with a consultant who will walk you through the findings and recommend your next move.',
  },
]

export default function ValuePillars() {
  return (
    <section id="how-it-works" className="scroll-mt-20 bg-white px-6 py-20">
      <div className="mx-auto max-w-[1280px]">
        <div className="mb-12 text-center">
          <h2 className="font-[family-name:var(--font-heading)] text-4xl tracking-wide text-[hsl(215_63%_14%)] md:text-5xl">
            HOW WE HELP YOUR PRACTICE WIN
          </h2>
          <p className="mt-3 text-[hsl(215_20%_55%)]">
            Four pillars of intelligence that give you a clear competitive edge.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {pillars.map(({ icon: Icon, title, body }) => (
            <div
              key={title}
              className="rounded-xl border border-[hsl(209_76%_95%)] bg-[hsl(209_76%_95%)] p-6 transition-shadow hover:shadow-md"
            >
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-[hsl(204_66%_52%)]">
                <Icon size={22} className="text-white" />
              </div>
              <h3 className="mb-2 font-[family-name:var(--font-body)] text-lg font-bold text-[hsl(215_63%_14%)]">
                {title}
              </h3>
              <p className="text-sm leading-relaxed text-[hsl(215_20%_45%)]">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
