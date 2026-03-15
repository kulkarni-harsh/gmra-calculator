import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { FileText } from 'lucide-react'
import type { Provider } from '@/types/api'

interface StepConfirmProps {
  specialtyName: string
  selectedProvider: Provider | null
  milesRadius: number
  email: string
  phone: string
  onGenerate: () => void
  onBack: () => void
}

export default function StepConfirm({
  specialtyName,
  selectedProvider,
  milesRadius,
  email,
  phone,
  onGenerate,
  onBack,
}: StepConfirmProps) {
  const providerAddress = selectedProvider
    ? [
        selectedProvider.location?.address_line_1,
        selectedProvider.location?.city,
        selectedProvider.location?.state,
        selectedProvider.location?.zip_code,
      ]
        .filter(Boolean)
        .join(', ')
    : '—'

  const rows = [
    { label: 'Report', value: 'Through-the-Door Codes Report ($500)' },
    { label: 'Specialty', value: specialtyName || '—' },
    { label: 'Practice', value: selectedProvider?.name ?? '—' },
    { label: 'Address', value: providerAddress },
    { label: 'Radius', value: `${milesRadius} miles` },
    { label: 'Email', value: email || '—' },
    { label: 'Phone', value: phone || 'Not provided' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-[family-name:var(--font-heading)] text-2xl tracking-wide text-white">
          STEP 4: REVIEW & GENERATE
        </h2>
        <p className="mt-1 text-sm text-white/60">
          Confirm your details before generating the report.
        </p>
      </div>

      {/* Order summary */}
      <div className="rounded-xl bg-[hsl(217_33%_17%)] p-6">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-white/60">
          Order Summary
        </h3>
        <div className="space-y-3">
          {rows.map(({ label, value }) => (
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

      {/* TODO: STRIPE PAYMENT INSERTION POINT
       * Before calling onGenerate(), this handler should:
       * 1. Create a Stripe PaymentIntent via POST /api/v2/payments/create-intent
       * 2. Confirm payment using Stripe.js / Stripe Elements
       * 3. Only proceed to onGenerate() on payment success
       *
       * Example:
       *   const { clientSecret } = await createPaymentIntent({ amount: 50000, currency: 'usd' })
       *   const result = await stripe.confirmPayment({ elements, clientSecret, ... })
       *   if (result.error) { setPaymentError(result.error.message); return }
       *
       * For now, payment is skipped and report generates directly.
       */}

      <Button
        onClick={onGenerate}
        size="lg"
        className="w-full gap-2 bg-[hsl(204_66%_52%)] py-6 text-base font-bold uppercase tracking-wide text-white hover:bg-[hsl(204_66%_45%)]"
      >
        <FileText size={20} />
        Generate My Comprehensive Report — $500
      </Button>

      <p className="text-center text-xs text-white/40">
        Comprehensive PDF report generated within ~5 minutes.
      </p>

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
