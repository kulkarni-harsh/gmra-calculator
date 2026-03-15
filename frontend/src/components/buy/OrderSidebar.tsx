import { Separator } from '@/components/ui/separator'
import { CheckCircle2, Shield, Flag, Calendar } from 'lucide-react'
import type { Provider } from '@/types/api'

interface OrderSidebarProps {
  specialtyName: string
  selectedProvider: Provider | null
  milesRadius: number
  email: string
  compact?: boolean
}

const INCLUDED = [
  'Competitive benchmarking',
  'Through-the-door CPT analysis',
  'Local demographics',
  'Comprehensive PDF report',
  'Provider density benchmark',
]

export default function OrderSidebar({
  specialtyName,
  selectedProvider,
  milesRadius,
  email,
  compact = false,
}: OrderSidebarProps) {
  const providerDisplay = selectedProvider?.name ?? '—'
  const specialtyDisplay = specialtyName || '—'
  const radiusDisplay = milesRadius ? `${milesRadius} miles` : '—'
  const emailDisplay = email || '—'

  if (compact) {
    return (
      <div className="flex items-center justify-between rounded-lg bg-[hsl(217_33%_17%)] px-4 py-3 text-sm text-white">
        <span className="font-[family-name:var(--font-heading)] tracking-wide">
          Through-the-Door Report
        </span>
        <span className="font-bold text-[hsl(204_66%_52%)]">$500</span>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-[hsl(217_33%_17%)] p-6 text-white">
      <h3 className="font-[family-name:var(--font-heading)] text-lg tracking-widest text-white/60">
        YOUR ORDER
      </h3>

      <Separator className="my-3 bg-white/10" />

      <p className="font-semibold leading-snug">Through-the-Door Codes Report</p>
      <p className="mt-0.5 text-2xl font-bold text-[hsl(204_66%_52%)]">$500</p>

      <Separator className="my-4 bg-white/10" />

      <div className="space-y-2 text-sm">
        {[
          { label: 'Practice', value: providerDisplay },
          { label: 'Specialty', value: specialtyDisplay },
          { label: 'Radius', value: radiusDisplay },
          { label: 'Email', value: emailDisplay },
        ].map(({ label, value }) => (
          <div key={label} className="flex justify-between gap-2">
            <span className="text-white/50">{label}</span>
            <span className="max-w-[150px] truncate text-right text-white/90">{value}</span>
          </div>
        ))}
      </div>

      <Separator className="my-4 bg-white/10" />

      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/50">
        WHAT&apos;S INCLUDED
      </p>
      <ul className="space-y-1.5">
        {INCLUDED.map((item) => (
          <li key={item} className="flex items-center gap-2 text-xs text-white/70">
            <CheckCircle2 size={13} className="shrink-0 text-[hsl(149_64%_29%)]" />
            {item}
          </li>
        ))}
      </ul>

      <Separator className="my-4 bg-white/10" />

      <div className="space-y-2 text-xs text-white/50">
        <div className="flex items-center gap-2">
          <Shield size={13} className="shrink-0" />
          HIPAA-conscious data handling
        </div>
        <div className="flex items-center gap-2">
          <Flag size={13} className="shrink-0" />
          US-only provider data
        </div>
        <div className="flex items-center gap-2">
          <Calendar size={13} className="shrink-0" />
          Delivered within 5 business days
        </div>
      </div>
    </div>
  )
}
