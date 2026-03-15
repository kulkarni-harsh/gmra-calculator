import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, Search } from 'lucide-react'
import { FormField, StyledInput, StyledSelect } from '@/components/buy/FormField'
import ProviderList from '@/components/buy/ProviderList'
import type { Provider, RadiusOption } from '@/types/api'

const RADIUS_OPTIONS: RadiusOption[] = [2, 5, 7, 10]

interface StepLocationProps {
  zipCode: string
  milesRadius: number
  onZipChange: (v: string) => void
  onRadiusChange: (v: number) => void
  onSearch: (zip: string, specialty: string) => void
  isSearching: boolean
  searchError: string | null
  hasSearched: boolean
  providers: Provider[]
  selectedProvider: Provider | null
  onSelectProvider: (p: Provider | null) => void
  specialtyName: string
  onNext: () => void
  onBack: () => void
}

export default function StepLocation({
  zipCode,
  milesRadius,
  onZipChange,
  onRadiusChange,
  onSearch,
  isSearching,
  searchError,
  hasSearched,
  providers,
  selectedProvider,
  onSelectProvider,
  specialtyName,
  onNext,
  onBack,
}: StepLocationProps) {
  const [zipError, setZipError] = useState('')

  const validateZip = (v: string) => {
    if (!/^\d{5}$/.test(v)) {
      setZipError('Please enter a valid 5-digit US zip code')
      return false
    }
    setZipError('')
    return true
  }

  const handleSearch = () => {
    if (!validateZip(zipCode)) return
    onSearch(zipCode, specialtyName)
  }

  const handleZipInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 5)
    onZipChange(val)
    if (zipError && /^\d{5}$/.test(val)) setZipError('')
  }

  return (
    <div className="space-y-7">
      <div>
        <h2 className="font-[family-name:var(--font-heading)] text-2xl tracking-wide text-white">
          STEP 2: FIND YOUR PRACTICE
        </h2>
        <p className="mt-1 text-sm text-white/50">
          Enter your practice&apos;s zip code to locate it in our provider database.
        </p>
      </div>

      {/* Zip + Radius + Search */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <FormField label="Zip Code" required error={zipError} className="flex-1">
          <StyledInput
            value={zipCode}
            onChange={handleZipInput}
            onBlur={() => zipCode && validateZip(zipCode)}
            placeholder="e.g. 90210"
            inputMode="numeric"
            pattern="[0-9]{5}"
            maxLength={5}
            hasError={!!zipError}
          />
        </FormField>

        <FormField label="Search Radius" className="w-full sm:w-44">
          <StyledSelect
            value={String(milesRadius)}
            onChange={(e) => onRadiusChange(Number(e.target.value))}
            options={RADIUS_OPTIONS.map((r) => ({ value: String(r), label: `${r} miles` }))}
          />
        </FormField>

        <div className="pb-0 sm:pb-0">
          <Button
            onClick={handleSearch}
            disabled={isSearching || !zipCode || !specialtyName}
            size="lg"
            className="h-[46px] gap-2 bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)] disabled:opacity-35"
          >
            {isSearching ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Searching…
              </>
            ) : (
              <>
                <Search size={16} />
                Find Practices
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Error */}
      {searchError && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-900/20 p-4">
          <AlertCircle size={15} className="mt-0.5 shrink-0 text-red-400" />
          <p className="text-sm text-red-300">{searchError}. Please try again.</p>
        </div>
      )}

      {/* Loading skeletons */}
      {isSearching && (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl bg-white/6" />
          ))}
        </div>
      )}

      {/* Provider results */}
      {!isSearching && hasSearched && !searchError && (
        <div>
          {providers.length === 0 ? (
            <div className="rounded-xl border border-white/8 bg-white/4 p-6 text-center">
              <p className="text-sm font-medium text-white/60">No providers found in this area.</p>
              <p className="mt-1 text-xs text-white/35">
                Try a different zip code or increase the search radius.
              </p>
            </div>
          ) : (
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-white/40">
                {providers.length} practice{providers.length !== 1 ? 's' : ''} found — select yours
              </p>
              <ProviderList
                providers={providers}
                selected={selectedProvider}
                onSelect={onSelectProvider}
              />
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-2">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-white/50 hover:bg-white/8 hover:text-white"
        >
          ← Back
        </Button>
        <Button
          onClick={onNext}
          disabled={!selectedProvider}
          size="lg"
          className="gap-2 bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)] disabled:opacity-35"
        >
          Next: Contact →
        </Button>
      </div>
    </div>
  )
}
