import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { FormField, StyledInput } from '@/components/buy/FormField'
import type { T0Location, RadiusOption } from '@/types/api'

const RADIUS_OPTIONS: { value: RadiusOption; label: string }[] = [
  { value: 5,  label: '5 miles' },
  { value: 10, label: '10 miles' },
  { value: 25, label: '25 miles' },
  { value: 50, label: '50 miles' },
]

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
  'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
  'VA','WA','WV','WI','WY','DC',
]

interface StepAddressProps {
  location: T0Location
  milesRadius: RadiusOption
  onLocationChange: (loc: T0Location) => void
  onRadiusChange: (radius: RadiusOption) => void
  onNext: () => void
  onBack: () => void
}

export default function StepAddress({
  location,
  milesRadius,
  onLocationChange,
  onRadiusChange,
  onNext,
  onBack,
}: StepAddressProps) {
  const [touched, setTouched] = useState(false)

  const set = (key: keyof T0Location, value: string) =>
    onLocationChange({ ...location, [key]: value })

  const isValid =
    location.address_line_1.trim().length > 0 &&
    location.city.trim().length > 0 &&
    location.state.length === 2 &&
    /^\d{5}$/.test(location.zip_code)

  const handleNext = () => {
    setTouched(true)
    if (isValid) onNext()
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-[family-name:var(--font-heading)] text-2xl tracking-wide text-white">
          STEP 2: YOUR LOCATION
        </h2>
        <p className="mt-1 text-sm text-white/60">
          Enter the address you want to analyze. We'll find all competitors within your chosen radius.
        </p>
      </div>

      <div className="space-y-4">
        <FormField label="Address Line 1" required error={touched && !location.address_line_1.trim() ? 'Required' : undefined}>
          <StyledInput
            placeholder="123 Main St"
            value={location.address_line_1}
            onChange={(e) => set('address_line_1', e.target.value)}
          />
        </FormField>

        <FormField label="Address Line 2 (optional)">
          <StyledInput
            placeholder="Suite 200"
            value={location.address_line_2 ?? ''}
            onChange={(e) => set('address_line_2', e.target.value)}
          />
        </FormField>

        <div className="grid grid-cols-2 gap-4">
          <FormField label="City" required error={touched && !location.city.trim() ? 'Required' : undefined}>
            <StyledInput
              placeholder="Austin"
              value={location.city}
              onChange={(e) => set('city', e.target.value)}
            />
          </FormField>

          <FormField label="State" required error={touched && location.state.length !== 2 ? 'Required' : undefined}>
            <Select value={location.state} onValueChange={(v) => set('state', v)}>
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
              onChange={(e) => set('zip_code', e.target.value.replace(/\D/g, ''))}
              hasError={touched && !/^\d{5}$/.test(location.zip_code)}
            />
          </FormField>

          <FormField label="Search Radius">
            <Select
              value={String(milesRadius)}
              onValueChange={(v) => onRadiusChange(Number(v) as RadiusOption)}
            >
              <SelectTrigger className="border-white/20 bg-white/5 text-white focus:border-[hsl(204_66%_52%)]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[hsl(217_33%_17%)] text-white">
                {RADIUS_OPTIONS.map((r) => (
                  <SelectItem key={r.value} value={String(r.value)} className="focus:bg-white/10">
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>
        </div>
      </div>

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
