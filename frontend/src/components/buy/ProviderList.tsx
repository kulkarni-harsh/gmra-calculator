import { useState } from 'react'
import { Search, MapPin, CreditCard, Building2, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Provider } from '@/types/api'

interface ProviderListProps {
  providers: Provider[]
  selected: Provider | null
  onSelect: (p: Provider) => void
}

function getInitials(name: string | null): string {
  if (!name) return '?'
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}

function formatAddress(p: Provider): string {
  return (
    [p.location?.address_line_1, p.location?.city, p.location?.state, p.location?.zip_code]
      .filter(Boolean)
      .join(', ') || 'Address not available'
  )
}

export default function ProviderList({ providers, selected, onSelect }: ProviderListProps) {
  const [query, setQuery] = useState('')

  const filtered = query.trim()
    ? providers.filter(
        (p) =>
          p.name?.toLowerCase().includes(query.toLowerCase()) ||
          formatAddress(p).toLowerCase().includes(query.toLowerCase()) ||
          p.npi?.includes(query) ||
          p.taxonomy?.description?.toLowerCase().includes(query.toLowerCase()),
      )
    : providers

  return (
    <div className="space-y-3">
      {/* Search filter */}
      {providers.length > 5 && (
        <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-[hsl(215_63%_10%)] px-3 py-2.5">
          <Search size={14} className="shrink-0 text-white/40" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by name, address, or NPI..."
            className="flex-1 bg-transparent text-sm text-white placeholder:text-white/30 outline-none"
          />
        </div>
      )}

      {/* Provider cards */}
      <div className="max-h-[420px] space-y-2 overflow-y-auto pr-0.5 [scrollbar-color:rgba(255,255,255,0.15)_transparent] [scrollbar-width:thin]">
        {filtered.length === 0 ? (
          <p className="py-4 text-center text-sm text-white/40">No providers match your search.</p>
        ) : (
          filtered.map((p) => {
            const isSelected = selected?.id === p.id
            const initials = getInitials(p.name)
            const address = formatAddress(p)
            const taxonomy = p.taxonomy?.description ?? null
            const affiliation = p.affiliation?.name ?? null

            return (
              <button
                key={p.id}
                type="button"
                onClick={() => onSelect(p)}
                className={cn(
                  'group w-full rounded-xl border p-4 text-left transition-all',
                  isSelected
                    ? 'border-[hsl(204_66%_52%)] bg-[hsl(204_66%_52%)/10] ring-2 ring-[hsl(204_66%_52%)/25]'
                    : 'border-white/10 bg-[hsl(215_63%_10%)] hover:border-white/25 hover:bg-[hsl(215_63%_12%)]',
                )}
              >
                <div className="flex items-start gap-3">
                  {/* Avatar */}
                  <div
                    className={cn(
                      'flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-sm font-bold',
                      isSelected
                        ? 'bg-[hsl(204_66%_52%)] text-white'
                        : 'bg-white/10 text-white/70 group-hover:bg-white/15',
                    )}
                  >
                    {initials}
                  </div>

                  {/* Details */}
                  <div className="min-w-0 flex-1">
                    {/* Name row */}
                    <div className="flex items-center justify-between gap-2">
                      <p
                        className={cn(
                          'truncate font-semibold leading-tight',
                          isSelected ? 'text-white' : 'text-white/90',
                        )}
                      >
                        {p.name ?? 'Unknown Provider'}
                      </p>
                      {isSelected && (
                        <span className="flex shrink-0 items-center gap-1 rounded-full bg-[hsl(204_66%_52%)] px-2 py-0.5 text-[10px] font-bold text-white">
                          <Check size={10} />
                          Selected
                        </span>
                      )}
                    </div>

                    {/* Taxonomy */}
                    {taxonomy && (
                      <p className="mt-0.5 truncate text-xs font-medium text-[hsl(204_66%_52%)]">
                        {taxonomy}
                      </p>
                    )}

                    {/* Address */}
                    <div className="mt-1.5 flex items-start gap-1.5 text-xs text-white/50">
                      <MapPin size={11} className="mt-0.5 shrink-0" />
                      <span className="leading-tight">{address}</span>
                    </div>

                    {/* Meta row */}
                    <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1">
                      {p.npi && (
                        <span className="flex items-center gap-1 text-[10px] text-white/35">
                          <CreditCard size={9} />
                          NPI: {p.npi}
                        </span>
                      )}
                      {affiliation && (
                        <span className="flex items-center gap-1 text-[10px] text-white/35">
                          <Building2 size={9} />
                          <span className="max-w-[160px] truncate">{affiliation}</span>
                        </span>
                      )}
                      {p.affiliation?.is_sole_proprietor && (
                        <span className="rounded bg-white/5 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-white/30">
                          Sole Proprietor
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            )
          })
        )}
      </div>

      {/* Count footer */}
      <p className="text-right text-[10px] text-white/25">
        Showing {filtered.length} of {providers.length} providers
      </p>
    </div>
  )
}
