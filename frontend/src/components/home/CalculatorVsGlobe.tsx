const CALC_BULLETS: ReadonlyArray<string> = [
  'An independent market intelligence tool operated by MCREC Reports LLC',
  'MCREC LLC owns the patent and is managing partner for reports',
  'MCREC Reports LLC holds the AlphaSophia data agreement',
  "Inspired by 25 years of Globe's fiduciary work with independent practices",
  'Available directly to any independently growing practice',
  'Order direct, receive your data, use it however you choose',
  'Powered by AlphaSophia · Patent Pending · Trademark Registered',
  'Does not require any Globe engagement — ever',
  'Does not create any brokerage relationship by ordering',
]

const GMRA_BULLETS: ReadonlyArray<string> = [
  'Physician-side tenant representation, fiduciary standard, nationally',
  '25 years exclusively representing independent physicians and non-hospital-owned groups',
  'Uses clinical demand analysis as the first step in every engagement',
  'Has never represented a hospital, health system, or landlord',
  'Globe fiduciary clients receive the Advanced Practice report at no cost',
  'Calculator users are never required to contact or engage Globe',
]

interface CardProps {
  eyebrow: string
  eyebrowColor: string
  title: string
  bullets: ReadonlyArray<string>
}

function SepCard({ eyebrow, eyebrowColor, title, bullets }: CardProps) {
  return (
    <div className="rounded-sm border border-mcrec-light p-7">
      <div className={`text-[9px] font-bold uppercase tracking-[3px] ${eyebrowColor}`}>
        {eyebrow}
      </div>
      <h3 className="mt-3 font-[family-name:var(--font-heading)] text-[22px] tracking-wide text-mcrec-navy">
        {title}
      </h3>
      <ul className="mt-3 space-y-1.5 text-xs leading-[1.6] text-mcrec-gray">
        {bullets.map((b) => (
          <li key={b} className="relative pl-4.5">
            <span className="absolute left-0 top-0 text-[10px] text-mcrec-teal">▸</span>
            {b}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function CalculatorVsGlobe() {
  return (
    <section id="globe-mcrec" className="bg-mcrec-off px-5 py-18 md:px-14 md:py-20">
      <div className="text-[10px] font-bold uppercase tracking-[4px] text-mcrec-teal">
        Two Separate Things
      </div>
      <h2 className="mt-3 font-[family-name:var(--font-heading)] text-[clamp(28px,4vw,42px)] leading-tight tracking-[2px] text-mcrec-navy">
        The Calculator and Globe Are <span className="text-mcrec-blue">Not the Same</span>
      </h2>
      <hr className="mt-4 mb-6 h-[3px] w-[60px] border-0 bg-gradient-to-r from-mcrec-blue to-mcrec-teal" />
      <p className="max-w-[640px] text-sm leading-[1.8] text-mcrec-gray">
        The calculator is an independent product. Globe is an independent brokerage firm. They share
        a conviction. They do not share a requirement.
      </p>

      <div className="mt-7 grid gap-6 md:grid-cols-2">
        <SepCard
          eyebrow="Independent Product"
          eyebrowColor="text-mcrec-teal"
          title="Medical Real Estate Calculator™"
          bullets={CALC_BULLETS}
        />
        <SepCard
          eyebrow="Fiduciary Brokerage Firm"
          eyebrowColor="text-mcrec-blue"
          title="Globe Medical Realty Advisors"
          bullets={GMRA_BULLETS}
        />
      </div>

      <div className="mt-5 rounded-sm border border-mcrec-light bg-white p-6 text-center">
        <p className="text-sm leading-[1.8] text-mcrec-gray">
          Globe built a tool because physicians needed data that only large hospital systems had.
          After 25 years of providing that analysis exclusively to Globe clients, MCREC LLC made it
          available as a standalone product — operated by MCREC Reports LLC — for any independently
          growing practice, with or without Globe. A physician can order every report we offer and
          never speak to a broker. A Globe client receives the top-tier report included in their
          engagement. These are two separate decisions. Neither one requires the other.
        </p>
      </div>
    </section>
  )
}
