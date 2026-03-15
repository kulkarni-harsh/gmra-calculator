import { useEffect, useRef, useState } from 'react'
import { ChevronDown, Search, Check, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Specialty } from '@/types/api'

interface SpecialtyComboboxProps {
  specialties: Specialty[]
  value: string
  onChange: (description: string) => void
}

export default function SpecialtyCombobox({ specialties, value, onChange }: SpecialtyComboboxProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selected = specialties.find((s) => s.description === value) ?? null

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Focus search input when opened
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50)
  }, [open])

  const filtered = query.trim()
    ? specialties.filter((s) =>
        s.description.toLowerCase().includes(query.toLowerCase()) ||
        s.taxonomy_codes.some((c) => c.toLowerCase().includes(query.toLowerCase())),
      )
    : specialties

  const handleSelect = (s: Specialty) => {
    onChange(s.description)
    setOpen(false)
    setQuery('')
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onChange('')
    setOpen(false)
    setQuery('')
  }

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'flex w-full items-center justify-between rounded-lg border px-4 py-3 text-left transition-all',
          'border-white/15 bg-[hsl(215_63%_10%)] text-white',
          'hover:border-[hsl(204_66%_52%)/50] hover:bg-[hsl(215_63%_12%)]',
          open && 'border-[hsl(204_66%_52%)] ring-2 ring-[hsl(204_66%_52%)/30]',
        )}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {selected ? (
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <div className="min-w-0 flex-1">
              <p className="truncate font-semibold text-white">{selected.description}</p>
              <p className="mt-0.5 text-xs text-white/40">
                {selected.taxonomy_codes.length} taxonomy code
                {selected.taxonomy_codes.length !== 1 ? 's' : ''}
                {selected.national_density != null && (
                  <span> · ~{selected.national_density} providers/100k nationally</span>
                )}
              </p>
            </div>
          </div>
        ) : (
          <span className="text-white/35">Select a specialty...</span>
        )}

        <div className="ml-2 flex shrink-0 items-center gap-1">
          {selected && (
            <span
              onClick={handleClear}
              className="flex h-5 w-5 items-center justify-center rounded-full text-white/40 hover:bg-white/10 hover:text-white"
            >
              <X size={12} />
            </span>
          )}
          <ChevronDown
            size={16}
            className={cn('text-white/40 transition-transform', open && 'rotate-180')}
          />
        </div>
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1.5 overflow-hidden rounded-xl border border-white/10 bg-[hsl(215_63%_10%)] shadow-2xl shadow-black/50">
          {/* Search bar */}
          <div className="flex items-center gap-2 border-b border-white/10 px-3 py-2.5">
            <Search size={14} className="shrink-0 text-white/40" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search specialties or taxonomy codes..."
              className="flex-1 bg-transparent text-sm text-white placeholder:text-white/30 outline-none"
            />
            {query && (
              <button onClick={() => setQuery('')} className="text-white/40 hover:text-white">
                <X size={12} />
              </button>
            )}
          </div>

          {/* Results */}
          <ul
            role="listbox"
            className="max-h-[340px] overflow-y-auto py-1 [scrollbar-color:rgba(255,255,255,0.15)_transparent] [scrollbar-width:thin]"
          >
            {filtered.length === 0 ? (
              <li className="px-4 py-6 text-center text-sm text-white/40">No specialties found</li>
            ) : (
              filtered.map((s) => {
                const isSelected = s.description === value
                const displayCodes = s.taxonomy_codes.slice(0, 4)
                const extra = s.taxonomy_codes.length - displayCodes.length

                return (
                  <li
                    key={s.id}
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => handleSelect(s)}
                    className={cn(
                      'group mx-1 cursor-pointer rounded-lg px-3 py-3 transition-colors',
                      isSelected
                        ? 'bg-[hsl(204_66%_52%)/15] text-white'
                        : 'text-white/80 hover:bg-white/5 hover:text-white',
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        {/* Name row */}
                        <div className="flex items-center gap-2">
                          <span className="font-semibold leading-tight">{s.description}</span>
                          <span className="shrink-0 rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-medium text-white/60">
                            {s.taxonomy_codes.length} Taxonomy codes
                          </span>
                        </div>

                        {/* Taxonomy code chips */}
                        {s.taxonomy_codes.length > 0 && (
                          <div className="mt-1.5 flex flex-wrap gap-1">
                            {displayCodes.map((code) => (
                              <span
                                key={code}
                                className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 font-mono text-[10px] text-white/45"
                              >
                                {code}
                              </span>
                            ))}
                            {extra > 0 && (
                              <span className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 font-mono text-[10px] text-white/30">
                                +{extra} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      {isSelected && (
                        <Check size={15} className="mt-0.5 shrink-0 text-[hsl(204_66%_52%)]" />
                      )}
                    </div>
                  </li>
                )
              })
            )}
          </ul>

          {/* Footer count */}
          <div className="border-t border-white/5 px-3 py-1.5 text-right text-[10px] text-white/25">
            {filtered.length} of {specialties.length} specialties
          </div>
        </div>
      )}
    </div>
  )
}
