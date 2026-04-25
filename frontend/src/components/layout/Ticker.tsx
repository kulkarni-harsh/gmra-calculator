const ITEMS: ReadonlyArray<{ text: string; gold?: boolean }> = [
  { text: 'Reports from $399 · Any Specialty · Any Market' },
  { text: 'Expanding · Renewing · Relocating · Know Before You Sign' },
  { text: 'Your Rent Is Your #2 Expense · Know What the Market Supports First' },
  { text: '25 Years · Fiduciary for Independent Physicians' },
  { text: 'No GMRA Engagement Required · Order Direct' },
  { text: 'Powered by AlphaSophia · MCREC Reports LLC' },
  { text: '2026 · Site Neutrality · New Decisions for Independent Practices', gold: true },
  { text: 'Patent Pending · Trademark Registered' },
]

export default function Ticker() {
  // Two copies side-by-side so the -50% translate creates a seamless loop.
  return (
    <div
      className="relative h-8 overflow-hidden border-b border-mcrec-blue/30 bg-mcrec-navy"
      role="marquee"
      aria-label="Key facts about Medical Real Estate Calculator"
    >
      <div className="flex h-8 w-max items-center animate-mcrec-tick">
        {[...ITEMS, ...ITEMS].map((item, i) => (
          <span
            key={i}
            aria-hidden={i >= ITEMS.length || undefined}
            className={`whitespace-nowrap px-7 text-[11px] font-medium uppercase tracking-[1.5px] ${
              item.gold ? 'text-mcrec-gold' : 'text-mcrec-gray2'
            }`}
          >
            {item.text}
          </span>
        ))}
      </div>
    </div>
  )
}
