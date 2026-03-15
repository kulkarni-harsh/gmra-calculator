import { cn } from '@/lib/utils'
import { AlertCircle } from 'lucide-react'
import type { ReactNode } from 'react'

interface FormFieldProps {
  label: string
  required?: boolean
  optional?: boolean
  hint?: string
  error?: string
  children: ReactNode
  className?: string
}

export function FormField({ label, required, optional, hint, error, children, className }: FormFieldProps) {
  return (
    <div className={cn('space-y-1.5', className)}>
      <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-white/50">
        {label}
        {required && <span className="text-[hsl(204_66%_52%)]">*</span>}
        {optional && <span className="font-normal normal-case tracking-normal text-white/30">(optional)</span>}
      </label>
      {children}
      {error ? (
        <p className="flex items-center gap-1.5 text-xs text-red-400">
          <AlertCircle size={11} className="shrink-0" />
          {error}
        </p>
      ) : hint ? (
        <p className="text-xs text-white/35">{hint}</p>
      ) : null}
    </div>
  )
}

// Styled input — use instead of shadcn Input for navy-theme forms
interface StyledInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean
  icon?: ReactNode
}

export function StyledInput({ hasError, icon, className, ...props }: StyledInputProps) {
  return (
    <div className="relative">
      {icon && (
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-white/30">
          {icon}
        </span>
      )}
      <input
        {...props}
        className={cn(
          'w-full rounded-lg border bg-[hsl(215_63%_10%)] px-4 py-3 text-sm text-white',
          'placeholder:text-white/25 outline-none transition-all',
          'border-white/12 hover:border-white/22',
          'focus:border-[hsl(204_66%_52%)] focus:ring-2 focus:ring-[hsl(204_66%_52%)/25]',
          hasError && 'border-red-500/60 focus:border-red-500 focus:ring-red-500/20',
          icon && 'pl-9',
          className,
        )}
      />
    </div>
  )
}

// Radius / small select — styled to match
interface StyledSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: { value: string; label: string }[]
}

export function StyledSelect({ options, className, ...props }: StyledSelectProps) {
  return (
    <select
      {...props}
      className={cn(
        'w-full appearance-none rounded-lg border border-white/12 bg-[hsl(215_63%_10%)]',
        'px-4 py-3 text-sm text-white outline-none transition-all',
        'hover:border-white/22',
        'focus:border-[hsl(204_66%_52%)] focus:ring-2 focus:ring-[hsl(204_66%_52%)/25]',
        // Custom chevron via background image
        "bg-[url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='rgba(255,255,255,0.35)' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E\")] bg-[right_12px_center] bg-no-repeat pr-9",
        className,
      )}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  )
}
