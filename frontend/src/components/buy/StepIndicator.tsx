import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

const steps = [
  { num: 1, label: 'Specialty' },
  { num: 2, label: 'Location' },
  { num: 3, label: 'Contact' },
  { num: 4, label: 'Review' },
  { num: 5, label: 'Payment' },
]

interface StepIndicatorProps {
  currentStep: number // 1-5
}

export default function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <div className="mb-8 flex items-center">
      {steps.map((step, idx) => {
        const isDone = currentStep > step.num
        const isCurrent = currentStep === step.num

        return (
          <div key={step.num} className="flex flex-1 items-center">
            {/* Circle */}
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition-colors',
                  isDone
                    ? 'bg-[hsl(204_66%_52%)] text-white'
                    : isCurrent
                      ? 'bg-[hsl(215_63%_14%)] text-white ring-2 ring-[hsl(204_66%_52%)]'
                      : 'bg-white/10 text-white/40',
                )}
              >
                {isDone ? <Check size={14} /> : step.num}
              </div>
              <span
                className={cn(
                  'mt-1 text-xs',
                  isCurrent ? 'font-semibold text-[hsl(204_66%_52%)]' : isDone ? 'text-white/70' : 'text-white/30',
                )}
              >
                {step.label}
              </span>
            </div>

            {/* Connector line */}
            {idx < steps.length - 1 && (
              <div
                className={cn(
                  'mx-1 mb-4 h-0.5 flex-1',
                  currentStep > step.num ? 'bg-[hsl(204_66%_52%)]' : 'bg-white/10',
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
