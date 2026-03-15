import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Lock, Mail, Phone } from 'lucide-react'
import { FormField, StyledInput } from '@/components/buy/FormField'

interface StepContactProps {
  email: string
  phone: string
  onEmailChange: (v: string) => void
  onPhoneChange: (v: string) => void
  onNext: () => void
  onBack: () => void
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_RE = /^\d{10}$/

export default function StepContact({
  email,
  phone,
  onEmailChange,
  onPhoneChange,
  onNext,
  onBack,
}: StepContactProps) {
  const [emailError, setEmailError] = useState('')
  const [phoneError, setPhoneError] = useState('')

  const validateEmail = (v: string) => {
    if (!EMAIL_RE.test(v)) {
      setEmailError('Please enter a valid email address')
      return false
    }
    setEmailError('')
    return true
  }

  const validatePhone = (v: string) => {
    if (!v) { setPhoneError(''); return true }
    const stripped = v.replace(/\D/g, '')
    if (!PHONE_RE.test(stripped)) {
      setPhoneError('Please enter a valid 10-digit phone number')
      return false
    }
    setPhoneError('')
    return true
  }

  const handleNext = () => {
    const emailOk = validateEmail(email)
    const phoneOk = validatePhone(phone)
    if (emailOk && phoneOk) onNext()
  }

  return (
    <div className="space-y-7">
      <div>
        <h2 className="font-[family-name:var(--font-heading)] text-2xl tracking-wide text-white">
          STEP 3: CONTACT INFORMATION
        </h2>
        <p className="mt-1 text-sm text-white/50">
          Where should we send your completed report?
        </p>
      </div>

      <div className="space-y-5">
        <FormField
          label="Your Email"
          required
          error={emailError}
          hint={emailError ? undefined : 'Your report will be sent here.'}
        >
          <StyledInput
            type="email"
            value={email}
            onChange={(e) => onEmailChange(e.target.value)}
            onBlur={() => email && validateEmail(email)}
            placeholder="you@yourpractice.com"
            hasError={!!emailError}
            icon={<Mail size={14} />}
          />
        </FormField>

        <FormField
          label="Phone Number"
          optional
          error={phoneError}
          hint={phoneError ? undefined : 'For your strategy call booking.'}
        >
          <StyledInput
            type="tel"
            value={phone}
            onChange={(e) => onPhoneChange(e.target.value)}
            onBlur={() => validatePhone(phone)}
            placeholder="(555) 123-4567"
            hasError={!!phoneError}
            icon={<Phone size={14} />}
          />
        </FormField>
      </div>

      {/* Privacy badge */}
      <div className="flex items-center gap-2.5 rounded-xl border border-white/8 bg-white/4 px-4 py-3.5">
        <Lock size={14} className="shrink-0 text-white/35" />
        <p className="text-xs leading-relaxed text-white/45">
          We never sell your data. Your email and phone are used only to deliver your report and schedule your strategy call.
        </p>
      </div>

      <div className="flex justify-between pt-2">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-white/50 hover:bg-white/8 hover:text-white"
        >
          ← Back
        </Button>
        <Button
          onClick={handleNext}
          disabled={!email}
          size="lg"
          className="gap-2 bg-[hsl(204_66%_52%)] font-bold text-white hover:bg-[hsl(204_66%_45%)] disabled:opacity-35"
        >
          Next: Review →
        </Button>
      </div>
    </div>
  )
}
