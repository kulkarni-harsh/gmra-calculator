import { Button } from '@/components/ui/button'
import { CheckCircle2, AlertTriangle, Home, Mail, Clock, Copy, MailX } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

interface ConfirmationScreenProps {
  providerName: string | null
  email: string
  htmlContent: string | null
  jobId?: string | null
  error: string | null
  onRetry: () => void
  onReset: () => void
}

export default function ConfirmationScreen({
  providerName,
  email,
  jobId,
  error,
  onRetry,
  onReset,
}: ConfirmationScreenProps) {
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)

  const copyTrackingId = () => {
    if (!jobId) return
    navigator.clipboard.writeText(jobId)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (error) {
    const isIneligibleEmail = error.toLowerCase().includes('ineligible customer email')

    if (isIneligibleEmail) {
      return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center px-6 py-20 text-center">
          <MailX size={56} className="mb-4 text-red-400" />
          <h2 className="font-[family-name:var(--font-heading)] text-3xl tracking-wide text-white">
            EMAIL NOT ELIGIBLE
          </h2>
          <p className="mt-2 max-w-md text-sm text-white/60">
            The email address you provided is not eligible for this service. Please use a valid business or professional email address.
          </p>
          <p className="mt-1 text-xs text-red-400/80">
            {/* Personal or disposable email domains are not accepted. */}
          </p>

          <div className="mt-8 flex gap-4">
            <Button
              onClick={onRetry}
              className="bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)]"
            >
              Use a Different Email
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
        ORDER CONFIRMED
      </h2>

      {providerName && (
        <p className="mt-2 text-white/70">
          Your MERC report for{' '}
          <span className="font-semibold text-white">{providerName}</span> is being generated.
        </p>
      )}

      {/* Email confirmation notice */}
      <div className="mt-5 flex items-start gap-3 rounded-xl border border-[hsl(204_66%_52%)]/30 bg-[hsl(204_66%_52%)]/10 px-5 py-4 text-left max-w-md">
        <Mail size={20} className="mt-0.5 shrink-0 text-[hsl(204_66%_52%)]" />
        <div>
          <p className="text-sm font-semibold text-white">Confirmation email sent</p>
          {email && (
            <p className="mt-0.5 text-sm text-white/60">
              We&apos;ve emailed your order confirmation and tracking ID to{' '}
              <span className="text-white/90">{email}</span>.
            </p>
          )}
        </div>
      </div>

      {/* Delivery timeline */}
      <div className="mt-3 flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 px-5 py-4 text-left max-w-md">
        <Clock size={20} className="mt-0.5 shrink-0 text-amber-400" />
        <div>
          <p className="text-sm font-semibold text-white">Report delivery: within 1 hour</p>
          <p className="mt-0.5 text-sm text-white/60">
            Your completed report will be delivered directly to your inbox — no need to stay on this page.
          </p>
        </div>
      </div>

      {/* Tracking ID */}
      {jobId && (
        <div className="mt-3 w-full max-w-md rounded-xl border border-white/10 bg-white/5 px-5 py-4 text-left">
          <p className="text-xs font-medium uppercase tracking-wider text-white/40">Tracking ID</p>
          <div className="mt-1.5 flex items-center gap-2">
            <p className="flex-1 font-mono text-sm text-white/90 break-all">{jobId}</p>
            <button
              onClick={copyTrackingId}
              className="shrink-0 rounded-md p-1.5 text-white/40 hover:bg-white/10 hover:text-white/80 transition-colors"
              title="Copy tracking ID"
            >
              <Copy size={14} />
            </button>
          </div>
          {copied && <p className="mt-1 text-xs text-[hsl(149_64%_45%)]">Copied!</p>}
          <p className="mt-2 text-xs text-white/40">
            Use this ID to check your report status anytime at{' '}
            <a href="/status" className="text-[hsl(204_66%_52%)] underline hover:text-[hsl(204_66%_65%)]">
              using this link
            </a>
          </p>
        </div>
      )}

      <p className="mt-4 text-sm text-white/50">
        Thank you for your order!
      </p>

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
