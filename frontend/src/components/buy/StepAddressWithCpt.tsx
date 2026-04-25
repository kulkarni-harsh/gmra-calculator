import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { FormField, StyledInput } from '@/components/buy/FormField'
import type { T1Location, DriveTimeOption } from '@/types/api'

const DRIVE_TIME_OPTIONS: { value: DriveTimeOption; label: string }[] = [
  { value: 5, label: '5 min drive' },
  { value: 10, label: '10 min drive' },
  { value: 15, label: '15 min drive' },
  { value: 30, label: '30 min drive' },
  { value: 45, label: '45 min drive' },
  { value: 60, label: '60 min drive' },
]

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
  'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
  'VA','WA','WV','WI','WY','DC',
]

interface StepAddressWithCptProps {
  location: T1Location
  driveTimeMinutes: DriveTimeOption
  cptCodes: string[]
  maxCptCodes?: number
  onLocationChange: (loc: T1Location) => void
  onDriveTimeChange: (v: DriveTimeOption) => void
  onCptCodesChange: (codes: string[]) => void
  onNext: () => void
  onBack: () => void
}

export default function StepAddressWithCpt({
  location,
  driveTimeMinutes,
  cptCodes,
  maxCptCodes = 5,
  onLocationChange,
  onDriveTimeChange,
  onCptCodesChange,
  onNext,
  onBack,
}: StepAddressWithCptProps) {
  const [touched, setTouched] = useState(false)

  const setLoc = (key: keyof T1Location, value: string) =>
    onLocationChange({ ...location, [key]: value })

  const setCptCode = (index: number, value: string) => {
    const updated = [...cptCodes]
    updated[index] = value.trim().toUpperCase()
    onCptCodesChange(updated)
  }

  const addCptCode = () => {
    if (cptCodes.length < maxCptCodes) onCptCodesChange([...cptCodes, ''])
  }

  const removeCptCode = (index: number) => {
    if (cptCodes.length <= 1) return
    onCptCodesChange(cptCodes.filter((_, i) => i !== index))
  }

  const isAddressValid =
    location.address_line_1.trim().length > 0 &&
    location.city.trim().length > 0 &&
    location.state.length === 2 &&
    /^\d{5}$/.test(location.zip_code)

  const isCptValid = cptCodes.length >= 1 && cptCodes.every((c) => c.trim().length > 0)

  const isValid = isAddressValid && isCptValid

  const handleNext = () => {
    setTouched(true)
    if (isValid) onNext()
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-[family-name:var(--font-heading)] text-2xl tracking-wide text-white">
          STEP 2: YOUR LOCATION & CPT CODES
        </h2>
        <p className="mt-1 text-sm text-white/60">
          Enter the address you want to analyze and the CPT codes you perform (up to 5).
        </p>
      </div>

      <div className="space-y-4">
        <FormField label="Address Line 1" required error={touched && !location.address_line_1.trim() ? 'Required' : undefined}>
          <StyledInput
            placeholder="123 Main St"
            value={location.address_line_1}
            onChange={(e) => setLoc('address_line_1', e.target.value)}
          />
        </FormField>

        <FormField label="Address Line 2 (optional)">
          <StyledInput
            placeholder="Suite 200"
            value={location.address_line_2 ?? ''}
            onChange={(e) => setLoc('address_line_2', e.target.value)}
          />
        </FormField>

        <div className="grid grid-cols-2 gap-4">
          <FormField label="City" required error={touched && !location.city.trim() ? 'Required' : undefined}>
            <StyledInput
              placeholder="Austin"
              value={location.city}
              onChange={(e) => setLoc('city', e.target.value)}
            />
          </FormField>

          <FormField label="State" required error={touched && location.state.length !== 2 ? 'Required' : undefined}>
            <Select value={location.state} onValueChange={(v) => setLoc('state', v)}>
              <SelectTrigger className="border-white/20 bg-white/5 text-white focus:border-[hsl(204_66%_52%)]">
                <SelectValue placeholder="State" />
              </SelectTrigger>
              <SelectContent className="max-h-60 bg-[hsl(217_33%_17%)] text-white">
                {US_STATES.map((s) => (
                  <SelectItem key={s} value={s} className="focus:bg-white/10">
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField label="ZIP Code" required error={touched && !/^\d{5}$/.test(location.zip_code) ? 'Enter a valid 5-digit ZIP' : undefined}>
            <StyledInput
              placeholder="78701"
              maxLength={5}
              value={location.zip_code}
              onChange={(e) => setLoc('zip_code', e.target.value.replace(/\D/g, ''))}
              hasError={touched && !/^\d{5}$/.test(location.zip_code)}
            />
          </FormField>

          <FormField label="Drive Time">
            <Select
              value={String(driveTimeMinutes)}
              onValueChange={(v) => onDriveTimeChange(Number(v) as DriveTimeOption)}
            >
              <SelectTrigger className="border-white/20 bg-white/5 text-white focus:border-[hsl(204_66%_52%)]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[hsl(217_33%_17%)] text-white">
                {DRIVE_TIME_OPTIONS.map((r) => (
                  <SelectItem key={r.value} value={String(r.value)} className="focus:bg-white/10">
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>
        </div>
      </div>

      {/* CPT Codes section */}
      <div className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-4">
        <div>
          <p className="text-sm font-semibold text-white">CPT Codes (1–{maxCptCodes})</p>
          <p className="mt-0.5 text-xs text-white/50">
            Enter the procedure codes you perform. These will be benchmarked against your local market.
          </p>
        </div>

        <div className="space-y-2">
          {cptCodes.map((code, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className="flex-1">
                <FormField
                  label={`CPT Code ${i + 1}`}
                  required
                  error={touched && !code.trim() ? 'Required' : undefined}
                >
                  <StyledInput
                    placeholder="e.g. 99213"
                    value={code}
                    onChange={(e) => setCptCode(i, e.target.value)}
                    hasError={touched && !code.trim()}
                  />
                </FormField>
              </div>
              {cptCodes.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeCptCode(i)}
                  className="mt-5 text-white/40 hover:text-red-400 transition-colors"
                  aria-label="Remove CPT code"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>

        {cptCodes.length < maxCptCodes && (
          <button
            type="button"
            onClick={addCptCode}
            className="text-sm text-[hsl(204_66%_52%)] hover:underline"
          >
            + Add another CPT code
          </button>
        )}
      </div>

      {touched && !isCptValid && (
        <p className="text-sm text-red-400">Please enter at least one CPT code.</p>
      )}

      <Button
        onClick={handleNext}
        size="lg"
        className="w-full bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)]"
      >
        Continue →
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
