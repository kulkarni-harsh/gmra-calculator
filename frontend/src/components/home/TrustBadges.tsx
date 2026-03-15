import { ShieldCheck, TrendingUp, MapPin } from 'lucide-react'

const badges = [
  {
    icon: ShieldCheck,
    label: 'Healthcare-focused analytics',
    sub: 'Built specifically for medical practice intelligence',
  },
  {
    icon: TrendingUp,
    label: 'Data-driven insights',
    sub: 'Powered by real Medicare, census, and provider data',
  },
  {
    icon: MapPin,
    label: 'Built for US provider offices',
    sub: 'Coverage across all 50 states with local benchmarks',
  },
]

export default function TrustBadges() {
  return (
    <section className="bg-white px-6 py-16">
      <div className="mx-auto max-w-[1280px]">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {badges.map(({ icon: Icon, label, sub }) => (
            <div
              key={label}
              className="flex flex-col items-center rounded-xl border border-[hsl(214_32%_91%)] p-6 text-center"
            >
              <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-full bg-[hsl(209_76%_95%)]">
                <Icon size={22} className="text-[hsl(211_73%_38%)]" />
              </div>
              <p className="font-semibold text-[hsl(215_63%_14%)]">{label}</p>
              <p className="mt-1 text-sm text-[hsl(215_20%_55%)]">{sub}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
