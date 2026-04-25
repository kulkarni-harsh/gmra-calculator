import FounderQuote from '@/components/home/FounderQuote'

interface Card {
  num: string
  title: string
  body: string
  tag?: string
}

const CARDS: ReadonlyArray<Card> = [
  {
    num: '01',
    title: 'Evaluating a New Location',
    body: 'Before committing to a new space, understand what the market in your drive-time area actually supports for your specialty — provider volume, procedure activity, and diagnosis demand.',
  },
  {
    num: '02',
    title: 'Negotiating a Lease Renewal',
    body: "A lease renewal is a major financial commitment. Market data on your location's income-producing factors gives you an objective foundation — regardless of who represents you or whether you use any broker at all.",
  },
  {
    num: '03',
    title: 'Planning a Practice Expansion',
    body: 'Adding a location, adding a provider, or entering a new market — clinical demand analysis tells you whether the market supports the growth before you invest in it.',
  },
  {
    num: '04',
    title: 'Evaluating Independence from a Hospital System',
    body: 'If site neutrality is changing the economics of your current employment arrangement, you need to know what the market supports before you make the move. This is exactly the first step.',
    tag: '2026 Opportunity',
  },
]

export default function WhoItsFor() {
  return (
    <section id="who-its-for" className="bg-mcrec-off px-5 py-18 md:px-14 md:py-20">
      <div className="text-[10px] font-bold uppercase tracking-[4px] text-mcrec-teal">
        Who It's For
      </div>
      <h2 className="mt-3 font-[family-name:var(--font-heading)] text-[clamp(28px,4vw,42px)] leading-tight tracking-[2px] text-mcrec-navy">
        Built for Independently Growing <span className="text-mcrec-blue">Practices</span> at Every
        Stage
      </h2>
      <hr className="mt-4 mb-6 h-[3px] w-[60px] border-0 bg-gradient-to-r from-mcrec-blue to-mcrec-teal" />
      <p className="max-w-[640px] text-sm leading-[1.8] text-mcrec-gray">
        Solo physicians through large multi-specialty groups. Any size, any specialty. The only
        requirement is that you operate outside a hospital system.
      </p>

      <div className="mt-7 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {CARDS.map((c) => (
          <div
            key={c.num}
            className="relative rounded-sm border border-mcrec-light bg-white p-7 hover:border-mcrec-blue"
          >
            <div className="font-[family-name:var(--font-heading)] text-[32px] leading-none text-mcrec-light">
              {c.num}
            </div>
            <div className="mt-2 text-sm font-bold text-mcrec-navy">{c.title}</div>
            <div className="mt-2 text-xs leading-[1.7] text-mcrec-gray">{c.body}</div>
            {c.tag && (
              <span className="absolute right-3 top-3 rounded-sm border border-mcrec-gold/30 bg-mcrec-gold/10 px-2 py-1 text-[8px] font-bold uppercase tracking-[1.5px] text-mcrec-gold">
                {c.tag}
              </span>
            )}
          </div>
        ))}
      </div>

      <FounderQuote />

      <p className="mt-6 text-center text-[11px] leading-[1.7] text-mcrec-gray">
        The Medical Real Estate Calculator™ is available to any independently growing practice.
        Ordering a report does not create any engagement with Globe Medical Realty Advisors, does
        not create any brokerage relationship, and carries no follow-up obligation of any kind. The
        data is yours to use however you choose.
      </p>
    </section>
  )
}
