import { Button } from '@/components/ui/button'
import { CheckCircle2, AlertTriangle, ExternalLink, Home } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { openHtmlInNewTab } from '@/lib/api'

interface ConfirmationScreenProps {
  providerName: string | null
  email: string
  htmlContent: string | null
  error: string | null
  onRetry: () => void
  onReset: () => void
}

export default function ConfirmationScreen({
  providerName,
  email,
  htmlContent,
  error,
  onRetry,
  onReset,
}: ConfirmationScreenProps) {
  const navigate = useNavigate()

  if (error) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-6 py-20 text-center">
        <AlertTriangle size={56} className="mb-4 text-amber-400" />
        <h2 className="font-[family-name:var(--font-heading)] text-3xl tracking-wide text-white">
          REPORT GENERATION FAILED
        </h2>
        <p className="mt-2 max-w-md text-sm text-white/60">
          We encountered an issue generating your report. Your information has been saved.
        </p>
        <p className="mt-1 text-xs text-red-400">{error}</p>

        <div className="mt-8 flex gap-4">
          <Button
            onClick={onRetry}
            className="bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)]"
          >
            Try Again
          </Button>
          <Button
            variant="outline"
            asChild
            className="border-white/30 text-white hover:bg-white/10"
          >
            <a href="mailto:support@mrec.com">Contact Support</a>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-6 py-20 text-center">
      <CheckCircle2 size={64} className="mb-4 text-[hsl(149_64%_29%)]" />

      <h2 className="font-[family-name:var(--font-heading)] text-4xl tracking-wide text-white">
        YOUR REPORT IS ON ITS WAY
      </h2>

      {providerName && (
        <p className="mt-2 text-white/70">
          We&apos;re preparing your MREC report for{' '}
          <span className="font-semibold text-white">{providerName}</span>.
        </p>
      )}

      {email && (
        <p className="mt-1 text-sm text-white/50">
          A copy will be sent to <span className="text-white/80">{email}</span>.
        </p>
      )}

      <p className="mt-2 text-sm text-white/50">
        Your consultant will reach out within 24 hours to schedule your strategy call.
      </p>

      {htmlContent && (
        <div className="mt-6 space-y-3">
          <p className="text-sm text-white/60">A download started automatically.</p>
          <Button
            onClick={() => openHtmlInNewTab(htmlContent)}
            className="gap-2 bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)]"
          >
            <ExternalLink size={16} />
            View Report Again
          </Button>
        </div>
      )}

      <div className="mt-8 flex gap-4">
        <Button
          onClick={() => navigate('/')}
          className="gap-2 bg-white/10 text-white hover:bg-white/20"
        >
          <Home size={16} />
          Back to Home
        </Button>
        <Button
          variant="outline"
          onClick={onReset}
          className="border-white/30 text-white hover:bg-white/10"
        >
          Generate Another Report
        </Button>
      </div>
    </div>
  )
}
