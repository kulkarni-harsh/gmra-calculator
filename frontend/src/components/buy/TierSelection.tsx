import { Lock, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { TIER_PRICES } from '@/lib/pricing'

interface TierFeature {
  label: string
  note?: string
}

const ALL_FEATURES: TierFeature[] = [
  { label: 'Market demand snapshot' },
  { label: 'Through-the-door CPT code analysis' },
  { label: 'Local demographics analysis' },
  { label: 'Provider density benchmark' },
  { label: 'AI insights PDF report' },
  { label: 'Anonymized provider market share breakdown' },
  { label: 'Custom CPT codes (up to 5)' },
  { label: 'Custom CPT codes (up to 15)' },
  { label: 'Gap & opportunity report', note: '*' },
  { label: '1-on-1 strategy call' },
]

const tiers = [
  {
    id: 0 as const,
    name: 'Market Entry Report',
    subtitle: 'Ground-level demand analysis',
    price: TIER_PRICES[0],
    badge: 'New',
    locked: false,
    included: new Set([
      'Market demand snapshot',
      'Through-the-door CPT code analysis',
      'Local demographics analysis',
      'Provider density benchmark',
      'AI insights PDF report',
    ]),
  },
  {
    id: 1 as const,
    name: 'Current Market Analysis',
    subtitle: 'CPT codes + anonymized market share',
    price: TIER_PRICES[1],
    badge: 'Most Popular',
    locked: false,
    included: new Set([
      'Market demand snapshot',
      'Through-the-door CPT code analysis',
      'Local demographics analysis',
      'Provider density benchmark',
      'AI insights PDF report',
      'Anonymized provider market share breakdown',
      'Custom CPT codes (up to 5)',
    ]),
  },
  {
    id: 2 as const,
    name: 'In-depth Market Analysis',
    subtitle: 'Up to 15 CPT codes + gaps report',
    price: TIER_PRICES[2],
    badge: 'New',
    locked: false,
    included: new Set([
      'Market demand snapshot',
      'Through-the-door CPT code analysis',
      'Local demographics analysis',
      'Provider density benchmark',
      'AI insights PDF report',
      'Anonymized provider market share breakdown',
      'Custom CPT codes (up to 5)',
      'Custom CPT codes (up to 15)',
      'Gap & opportunity report',
    ]),
  },
  {
    id: 3 as const,
    name: 'Custom Market Expansion Report',
    subtitle: 'Expert consultation included',
    price: TIER_PRICES[3],
    badge: 'Expert Call',
    locked: true,
    included: new Set([
      'Market demand snapshot',
      'Through-the-door CPT code analysis',
      'Local demographics analysis',
      'Provider density benchmark',
      'AI insights PDF report',
      'Anonymized provider market share breakdown',
      'Custom CPT codes (up to 5)',
      'Custom CPT codes (up to 15)',
      'Gap & opportunity report',
      '1-on-1 strategy call',
    ]),
  },
]

interface TierSelectionProps {
  selectedTierId: 0 | 1 | 2 | 3
  onSelect: (id: 0 | 1 | 2 | 3) => void
}

export default function TierSelection({ selectedTierId, onSelect }: TierSelectionProps) {
  return (
    <div className="mb-10">
      <h2 className="mb-6 font-[family-name:var(--font-heading)] text-3xl tracking-wide text-white">
        SELECT YOUR REPORT
      </h2>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
              {tier.subtitle && (
                <p className="mt-0.5 text-xs text-white/50">{tier.subtitle}</p>
              )}
              <p className="mt-1 text-3xl font-bold text-[hsl(204_66%_52%)]">{tier.price}</p>

              {/* Feature list — shows ALL features with ✓ included / ✗ not included */}
              <ul className="mt-4 space-y-1.5">
                {ALL_FEATURES.map((f) => {
                  const has = tier.included.has(f.label)
                  return (
                    <li
                      key={f.label}
                      className={cn(
                        'flex items-start gap-2 text-sm',
                        has ? 'text-white/80' : 'text-white/30',
                      )}
                    >
                      <span
                        className={cn(
                          'mt-0.5 shrink-0 font-bold',
                          has ? 'text-[hsl(204_66%_52%)]' : 'text-white/25',
                        )}
                      >
                        {has ? '✓' : '✗'}
                      </span>
                      {f.label}
                      {f.note && has && (
                        <sup className="text-white/40">{f.note}</sup>
                      )}
                    </li>
                  )
                })}
              </ul>

              <div className="mt-5">
                {tier.locked ? (
                  <Button disabled className="w-full cursor-not-allowed bg-white/10 text-white/40">
                    Contact Us
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
      <p className="mt-3 text-xs text-white/30">
        * Gap &amp; opportunity report is in development — included when available at no extra cost.
      </p>
    </div>
  )
}
