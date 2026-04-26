import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Phone } from 'lucide-react'

interface StepT4RequestProps {
  specialtyName: string
  email: string
  phone: string
  onSubmit: () => void
  onBack: () => void
}

export default function StepT4Request({
  specialtyName,
  email,
  phone,
  onSubmit,
  onBack,
}: StepT4RequestProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-[family-name:var(--font-heading)] text-2xl tracking-wide text-white">
          STEP 4: CUSTOM REPORT REQUEST
        </h2>
        <p className="mt-1 text-sm text-white/60">
          Our team will reach out within 1 business day to scope your custom report.
        </p>
      </div>

      <div className="rounded-xl bg-[hsl(217_33%_17%)] p-6 space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-white/60">Request Summary</h3>

        <div className="space-y-3">
          {[
            { label: 'Report', value: 'Custom Market Expansion Report ($999+)' },
            { label: 'Specialty', value: specialtyName || '—' },
            { label: 'Email', value: email || '—' },
            { label: 'Phone', value: phone || 'Not provided' },
          ].map(({ label, value }) => (
            <div key={label}>
              <div className="flex items-start justify-between gap-4 text-sm">
                <span className="shrink-0 text-white/50">{label}</span>
                <span className="text-right text-white/90">{value}</span>
              </div>
              <Separator className="mt-3 bg-white/5" />
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-[hsl(204_66%_52%)]/30 bg-[hsl(204_66%_52%)]/10 p-4 text-sm text-white/80">
        <p className="font-semibold text-white">What happens next?</p>
        <ul className="mt-2 space-y-1.5 text-white/70">
          <li>• A MREC consultant will call or email you within 1 business day.</li>
          <li>• You will define the scope, custom CPT codes, and analysis depth together.</li>
          <li>• Payment ($999+) is collected after scope is agreed upon.</li>
        </ul>
      </div>

      <Button
        onClick={onSubmit}
        size="lg"
        className="w-full gap-2 bg-[hsl(204_66%_52%)] py-6 text-base font-bold uppercase tracking-wide text-white hover:bg-[hsl(204_66%_45%)]"
      >
        <Phone size={20} />
        Submit Custom Report Request
      </Button>

      <div className="flex justify-start">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-white/60 hover:bg-white/10 hover:text-white"
        >
          ← Back
        </Button>
      </div>
    </div>
  )
}
