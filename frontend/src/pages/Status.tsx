import { useState } from 'react'
import { Search, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { checkJobStatus } from '@/lib/api'
import type { JobStatus } from '@/lib/api'

const STATUS_LABEL: Record<string, string> = {
  pending: 'Queued',
  running: 'Generating',
  done: 'Ready',
  failed: 'Failed',
}

const STATUS_COLOR: Record<string, string> = {
  pending: 'text-yellow-400',
  running: 'text-sky-400',
  done: 'text-green-400',
  failed: 'text-red-400',
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'running') return <Loader2 size={20} className="animate-spin text-sky-400" />
  if (status === 'done') return <CheckCircle size={20} className="text-green-400" />
  if (status === 'failed') return <XCircle size={20} className="text-red-400" />
  return <Clock size={20} className="text-yellow-400" />
}

export default function Status() {
  const [trackingId, setTrackingId] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<JobStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleCheck = async () => {
    const id = trackingId.trim()
    if (!id) return
    setIsLoading(true)
    setResult(null)
    setError(null)
    try {
      const data = await checkJobStatus(id)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lookup failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[hsl(215_63%_14%)]">
      <div className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="font-[family-name:var(--font-heading)] text-4xl tracking-wide text-white">
          CHECK REPORT STATUS
        </h1>
        <p className="mt-2 text-sm text-white/50">
          Enter the tracking ID from your confirmation email or screen.
        </p>

        <div className="mt-8 flex gap-3">
          <input
            type="text"
            value={trackingId}
            onChange={(e) => setTrackingId(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
            placeholder="MERC-XXXXXXXXXXXX"
            className="flex-1 rounded-lg border border-white/15 bg-white/8 px-4 py-3 font-mono text-sm text-white placeholder:text-white/30 focus:border-[hsl(204_66%_52%)] focus:outline-none"
          />
          <Button
            onClick={handleCheck}
            disabled={!trackingId.trim() || isLoading}
            className="gap-2 bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)] disabled:opacity-35"
          >
            {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            Check
          </Button>
        </div>

        {error && (
          <div className="mt-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-6 rounded-xl border border-white/10 bg-[hsl(217_33%_17%)] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <StatusIcon status={result.status} />
                <span className={`font-bold ${STATUS_COLOR[result.status] ?? 'text-white'}`}>
                  {STATUS_LABEL[result.status] ?? result.status}
                </span>
              </div>
              <span className="font-mono text-xs text-white/40">{result.job_id}</span>
            </div>

            <div className="space-y-1 border-t border-white/8 pt-4 text-sm text-white/60">
              {result.provider_name && (
                <p><span className="text-white/40">Provider:</span> {result.provider_name}</p>
              )}
              {result.specialty_name && (
                <p><span className="text-white/40">Specialty:</span> {result.specialty_name}</p>
              )}
              <p>
                <span className="text-white/40">Submitted:</span>{' '}
                {new Date(result.created_at).toLocaleString()}
              </p>
              <p>
                <span className="text-white/40">Last updated:</span>{' '}
                {new Date(result.updated_at).toLocaleString()}
              </p>
            </div>

            {result.status === 'done' && result.report_pdf_s3_url && (
              <div className="flex flex-wrap gap-3 border-t border-white/8 pt-4">
                <a
                  href={result.report_pdf_s3_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center rounded-md bg-[hsl(204_66%_52%)] px-4 py-2 text-sm font-bold text-white hover:bg-[hsl(204_66%_45%)]"
                >
                  Download PDF (7-day link)
                </a>
              </div>
            )}

            {result.status === 'failed' && result.error && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300 border-t">
                {result.error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
