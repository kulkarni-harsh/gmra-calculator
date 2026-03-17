import { useState } from 'react'
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { loadStripe } from '@stripe/stripe-js'
import { Button } from '@/components/ui/button'
import { Lock } from 'lucide-react'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY)

interface StepPaymentInnerProps {
  onSuccess: (paymentIntentId: string) => void
  onBack: () => void
}

function StepPaymentInner({ onSuccess, onBack }: StepPaymentInnerProps) {
  const stripe = useStripe()
  const elements = useElements()
  const [isPaying, setIsPaying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return

    setIsPaying(true)
    setError(null)

    const { error: stripeError, paymentIntent } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/buy`,
      },
      redirect: 'if_required',
    })

    if (stripeError) {
      setError(stripeError.message ?? 'Payment failed. Please try again.')
      setIsPaying(false)
      return
    }

    if (paymentIntent?.status === 'succeeded') {
      onSuccess(paymentIntent.id)
    } else {
      setError('Payment was not completed. Please try again.')
      setIsPaying(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-[family-name:var(--font-heading)] text-2xl tracking-wide text-white">
          STEP 5: PAYMENT
        </h2>
        <p className="mt-1 text-sm text-white/60">
          Secure payment powered by Stripe. Your card details never touch our servers.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-xl bg-white/5 p-4">
          <PaymentElement />
        </div>

        {error && (
          <p className="rounded-lg bg-red-900/30 px-4 py-3 text-sm text-red-300">{error}</p>
        )}

        <Button
          type="submit"
          disabled={!stripe || isPaying}
          size="lg"
          className="w-full gap-2 bg-[hsl(204_66%_52%)] py-6 text-base font-bold uppercase tracking-wide text-white hover:bg-[hsl(204_66%_45%)] disabled:opacity-60"
        >
          <Lock size={18} />
          {isPaying ? 'Processing…' : 'Pay $500 & Generate Report'}
        </Button>
      </form>

      <div className="flex justify-start">
        <Button
          variant="ghost"
          onClick={onBack}
          disabled={isPaying}
          className="text-white/60 hover:bg-white/10 hover:text-white"
        >
          ← Back
        </Button>
      </div>
    </div>
  )
}

interface StepPaymentProps {
  clientSecret: string
  onSuccess: (paymentIntentId: string) => void
  onBack: () => void
}

export default function StepPayment({ clientSecret, onSuccess, onBack }: StepPaymentProps) {
  return (
    <Elements
      stripe={stripePromise}
      options={{
        clientSecret,
        appearance: {
          theme: 'night',
          variables: {
            colorPrimary: 'hsl(204, 66%, 52%)',
            colorBackground: 'hsl(217, 33%, 17%)',
            colorText: '#ffffff',
            borderRadius: '8px',
          },
        },
      }}
    >
      <StepPaymentInner onSuccess={onSuccess} onBack={onBack} />
    </Elements>
  )
}
