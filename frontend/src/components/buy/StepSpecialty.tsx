import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { FormField } from '@/components/buy/FormField'
import SpecialtyCombobox from '@/components/buy/SpecialtyCombobox'
import type { Specialty } from '@/types/api'

interface StepSpecialtyProps {
  specialties: Specialty[]
  isLoading: boolean
  error: string | null
  value: string
  onChange: (v: string) => void
  onRetry: () => void
  onNext: () => void
}

export default function StepSpecialty({
  specialties,
  isLoading,
  error,
  value,
  onChange,
  onRetry,
  onNext,
}: StepSpecialtyProps) {
  return (
    <div className="space-y-7">
      <div>
        <h2 className="font-[family-name:var(--font-heading)] text-2xl tracking-wide text-white">
          STEP 1: SELECT YOUR SPECIALTY
        </h2>
        <p className="mt-1 text-sm text-white/50">
          Choose the specialty that best describes your practice.
        </p>
      </div>

      {error ? (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-900/20 p-4">
          <AlertCircle size={16} className="mt-0.5 shrink-0 text-red-400" />
          <div className="text-sm">
            <p className="font-medium text-red-300">Could not load specialties</p>
            <button
              onClick={onRetry}
              className="mt-2 flex items-center gap-1.5 text-xs text-red-400 underline hover:no-underline"
            >
              <RefreshCw size={11} />
              Try again
            </button>
          </div>
        </div>
      ) : isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-[60px] w-full rounded-lg bg-white/8" />
          <p className="text-xs text-white/30">Loading specialties…</p>
        </div>
      ) : (
        <FormField
          label="Medical Specialty"
          required
          hint={value ? undefined : `${specialties.length} specialties available`}
        >
          <SpecialtyCombobox specialties={specialties} value={value} onChange={onChange} />
        </FormField>
      )}

      <div className="flex justify-end pt-2">
        <Button
          onClick={onNext}
          disabled={!value}
          size="lg"
          className="gap-2 bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)] disabled:opacity-35"
        >
          Next: Location →
        </Button>
      </div>
    </div>
  )
}
