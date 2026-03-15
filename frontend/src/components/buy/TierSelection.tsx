import { Lock, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const tiers = [
  {
    id: 1 as const,
    name: 'Through-the-Door Codes Report',
    price: '$500',
    badge: 'Most Popular',
    locked: false,
    features: [
      'Competitive benchmarking vs. local providers',
      'Through-the-door CPT code analysis',
      'Local demographics analysis',
      'Comprehensive PDF report',
      'Provider density benchmark',
    ],
  },
  {
    id: 2 as const,
    name: '5-Code Strategic Report',
    price: '$599',
    badge: 'Coming Soon',
    locked: true,
    features: [
      'Everything in Tier 1',
      'Top 5 highest-revenue CPT codes analyzed',
      'Revenue forecast per procedure',
      'Procedure-specific demand analysis',
    ],
  },
  {
    id: 3 as const,
    name: '10-Code Full Analysis + Add-On',
    price: '$799',
    badge: 'Coming Soon',
    locked: true,
    features: [
      'Everything in Tier 2',
      'Complete procedure mix',
      'NP/PA peer presence analysis',
      'Payer mix breakdown',
      'Infrastructure sizing recommendations',
    ],
  },
]

interface TierSelectionProps {
  selectedTierId: 1 | 2 | 3
  onSelect: (id: 1 | 2 | 3) => void
}

export default function TierSelection({ selectedTierId, onSelect }: TierSelectionProps) {
  return (
    <div className="mb-10">
      <h2 className="mb-6 font-[family-name:var(--font-heading)] text-3xl tracking-wide text-white">
        SELECT YOUR REPORT
      </h2>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {tiers.map((tier) => {
          const isSelected = selectedTierId === tier.id

          return (
            <div
              key={tier.id}
              onClick={tier.locked ? undefined : () => onSelect(tier.id)}
              className={cn(
                'relative rounded-xl border-2 p-6 transition-all',
                tier.locked
                  ? 'cursor-not-allowed opacity-55 select-none'
                  : 'cursor-pointer hover:border-[hsl(204_66%_52%)]',
                isSelected && !tier.locked
                  ? 'border-[hsl(204_66%_52%)] bg-[hsl(217_33%_17%)] ring-2 ring-[hsl(204_66%_52%)]'
                  : 'border-white/20 bg-[hsl(217_33%_17%)]',
              )}
            >
              {/* Badge */}
              <span
                className={cn(
                  'absolute right-3 top-3 rounded-full px-2.5 py-0.5 text-xs font-bold',
                  tier.locked
                    ? 'bg-white/20 text-white/60'
                    : 'bg-[hsl(204_66%_52%)] text-white',
                )}
              >
                {tier.locked ? (
                  tier.badge
                ) : (
                  <span className="flex items-center gap-1">
                    <Star size={10} />
                    {tier.badge}
                  </span>
                )}
              </span>

              {/* Lock overlay */}
              {tier.locked && (
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center rounded-xl">
                  <Lock size={32} className="text-white/30" />
                </div>
              )}

              <h3 className="font-[family-name:var(--font-heading)] text-xl tracking-wide text-white">
                {tier.name}
              </h3>
              <p className="mt-1 text-3xl font-bold text-[hsl(204_66%_52%)]">{tier.price}</p>

              <ul className="mt-4 space-y-1.5">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-white/70">
                    <span className="mt-0.5 shrink-0 text-[hsl(204_66%_52%)]">✓</span>
                    {f}
                  </li>
                ))}
              </ul>

              <div className="mt-5">
                {tier.locked ? (
                  <Button disabled className="w-full cursor-not-allowed bg-white/10 text-white/40">
                    Coming Soon
                  </Button>
                ) : (
                  <Button
                    onClick={() => onSelect(tier.id)}
                    className={cn(
                      'w-full font-bold',
                      isSelected
                        ? 'bg-[hsl(204_66%_52%)] text-white'
                        : 'bg-white/10 text-white hover:bg-[hsl(204_66%_52%)]',
                    )}
                  >
                    {isSelected ? '✓ Selected' : 'Select This Report'}
                  </Button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
