import { useEffect, useState } from 'react'
import { Progress } from '@/components/ui/progress'

const STEPS = [
  { label: 'Locating your practice...', durationMs: 8_000 },
  { label: 'Fetching competitor providers...', durationMs: 50_000 },
  { label: 'Analyzing procedure volumes...', durationMs: 60_000 },
  { label: 'Calculating Medicare rates...', durationMs: 30_000 },
  { label: 'Pulling census demographics...', durationMs: 20_000 },
  { label: 'Computing density benchmarks...', durationMs: 20_000 },
  { label: 'Assembling your report...', durationMs: 30_000 },
]

const TOTAL_MS = STEPS.reduce((acc, s) => acc + s.durationMs, 0)
const MAX_PCT = 95

interface GeneratingScreenProps {
  providerName: string | null
}

export default function GeneratingScreen({ providerName }: GeneratingScreenProps) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const start = Date.now()
    const id = setInterval(() => {
      setElapsed(Date.now() - start)
    }, 500)
    return () => clearInterval(id)
  }, [])

  // Compute progress percentage (capped at MAX_PCT)
  const pct = Math.min((elapsed / TOTAL_MS) * MAX_PCT, MAX_PCT)

  // Determine current step label
  let acc = 0
  let currentLabel = STEPS[STEPS.length - 1].label
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
        GENERATING YOUR REPORT
      </h2>

      {providerName && (
        <p className="mt-2 text-white/60">
          Analyzing{' '}
          <span className="font-semibold text-white">{providerName}</span>{' '}
          against the local market.
        </p>
      )}

      <p className="mt-1 text-sm text-white/40">
        This typically takes 3–5 minutes — please keep this tab open.
      </p>

      {/* Progress bar */}
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
        Do not close or refresh this tab while your report is being generated.
      </p>
    </div>
  )
}
