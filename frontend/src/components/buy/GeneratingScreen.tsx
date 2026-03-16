import { useEffect, useState } from 'react'
import { Progress } from '@/components/ui/progress'
import { CheckCircle2, Mail, Clock, Copy } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'

const STEPS = [
  { label: 'Verifying your practice...', durationMs: 2_000 },
  { label: 'Confirming your order...', durationMs: 3_000 },
  { label: 'Queuing your report...', durationMs: 3_000 },
]

const TOTAL_MS = STEPS.reduce((acc, s) => acc + s.durationMs, 0)
const MAX_PCT = 95

interface GeneratingScreenProps {
  providerName: string | null
  email?: string
  jobId?: string | null
  onReset?: () => void
}

export default function GeneratingScreen({ providerName, email, jobId, onReset }: GeneratingScreenProps) {
  const [elapsed, setElapsed] = useState(0)
  const [copied, setCopied] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (jobId) return // stop ticking once queued
    const start = Date.now()
    const id = setInterval(() => setElapsed(Date.now() - start), 200)
    return () => clearInterval(id)
  }, [jobId])

  const copyTrackingId = () => {
    if (!jobId) return
    navigator.clipboard.writeText(jobId)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // ── Queued / thank-you state ──────────────────────────────────────────────
  if (jobId) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-6 py-20 text-center">
        <CheckCircle2 size={64} className="mb-4 text-[hsl(149_64%_29%)]" />

        <h2 className="font-[family-name:var(--font-heading)] text-4xl tracking-wide text-white">
          ORDER CONFIRMED
        </h2>

        {providerName && (
          <p className="mt-2 text-white/70">
            Your MERC report for{' '}
            <span className="font-semibold text-white">{providerName}</span> has been queued.
          </p>
        )}

        {/* Email notice */}
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-[hsl(204_66%_52%)]/30 bg-[hsl(204_66%_52%)]/10 px-5 py-4 text-left max-w-md w-full">
          <Mail size={20} className="mt-0.5 shrink-0 text-[hsl(204_66%_52%)]" />
          <div>
            <p className="text-sm font-semibold text-white">Report arriving via email</p>
            {email ? (
              <p className="mt-0.5 text-sm text-white/60">
                We&apos;ll deliver your completed report to{' '}
                <span className="text-white/90">{email}</span> within <span className="text-white font-medium">1 hour</span>.
              </p>
            ) : (
              <p className="mt-0.5 text-sm text-white/60">
                Your completed report will be delivered to your registered email within <span className="text-white font-medium">1 hour</span>.
              </p>
            )}
          </div>
        </div>

        {/* Delivery estimate */}
        <div className="mt-3 flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 px-5 py-4 text-left max-w-md w-full">
          <Clock size={20} className="mt-0.5 shrink-0 text-amber-400" />
          <div>
            <p className="text-sm font-semibold text-white">No need to stay on this page</p>
            <p className="mt-0.5 text-sm text-white/60">
              Your report generates in the background. You&apos;re free to close this tab — we&apos;ll email you when it&apos;s ready.
            </p>
          </div>
        </div>

        {/* Tracking ID */}
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
            Check your report status anytime {' '}
            <a
              href="/status"
              className="text-[hsl(204_66%_52%)] underline hover:text-[hsl(204_66%_65%)]"
            >
              using this link
            </a>
          </p>
        </div>

        <p className="mt-4 text-sm text-white/50">
          Thank you for your order!.
        </p>

        <div className="mt-8 flex gap-4">
          <Button
            onClick={() => navigate('/status')}
            className="bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)]"
          >
            Check Status
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate('/')}
            className="border-white/30 text-white hover:bg-white/10"
          >
            Back to Home
          </Button>
          {onReset && (
            <Button
              variant="outline"
              onClick={onReset}
              className="border-white/30 text-white hover:bg-white/10"
            >
              New Report
            </Button>
          )}
        </div>
      </div>
    )
  }

  // ── Submitting / loading state ────────────────────────────────────────────
  const pct = Math.min((elapsed / TOTAL_MS) * MAX_PCT, MAX_PCT)

  let acc = 0
  let currentLabel = 'Almost there — finalizing your order...'
  for (const step of STEPS) {
    acc += step.durationMs
    if (elapsed < acc) {
      currentLabel = step.label
      break
    }
  }

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-6 py-20 text-center">
      {/* Animated pulse ring */}
      <div className="relative mb-8 flex h-20 w-20 items-center justify-center">
        <div className="absolute inset-0 animate-ping rounded-full bg-[hsl(204_66%_52%)] opacity-20" />
        <div className="absolute inset-2 animate-pulse rounded-full bg-[hsl(204_66%_52%)] opacity-30" />
        <span className="relative font-[family-name:var(--font-heading)] text-2xl tracking-widest text-[hsl(204_66%_52%)]">
          M
        </span>
      </div>

      <h2 className="font-[family-name:var(--font-heading)] text-4xl tracking-wide text-white">
        PLACING YOUR ORDER
      </h2>

      {providerName && (
        <p className="mt-2 text-white/60">
          Submitting your report request for{' '}
          <span className="font-semibold text-white">{providerName}</span>.
        </p>
      )}

      <p className="mt-1 text-sm text-white/40">
        Just a moment while we confirm your order.
      </p>

      <div className="mt-8 w-full max-w-md">
        <Progress
          value={pct}
          className="h-2 bg-white/10 [&>div]:bg-[hsl(204_66%_52%)] [&>div]:transition-all [&>div]:duration-500"
        />
        <p className="mt-3 flex items-center justify-center gap-1.5 text-sm text-white/60">
          <span className="inline-flex gap-0.5">
            <span className="animate-bounce delay-0">•</span>
            <span className="animate-bounce delay-150">•</span>
            <span className="animate-bounce delay-300">•</span>
          </span>
          {currentLabel}
        </p>
      </div>

      <p className="mt-6 text-xs text-white/30">
        Your report will be delivered to your email within 1 hour.
      </p>
    </div>
  )
}
