interface MercLogoProps {
  variant?: 'nav' | 'footer'
}

export default function MercLogo({ variant = 'nav' }: MercLogoProps) {
  const isFooter = variant === 'footer'
  const baseColor = isFooter ? 'text-white' : 'text-mcrec-navy'
  const accentColor = 'text-mcrec-blue'
  const taglineColor = 'text-mcrec-teal'

  return (
    <div className={`leading-tight ${baseColor}`}>
      <div className="font-[family-name:var(--font-heading)] text-[18px] tracking-[2px]">
        MEDICAL <span className={accentColor}>REAL</span>
        <br />
        ESTATE <span className={accentColor}>CALCULATOR</span>™
      </div>
      <div className={`mt-0.5 text-[7px] font-bold uppercase tracking-[2.5px] ${taglineColor}`}>
        Clinical Demand. Precise Locations.
      </div>
    </div>
  )
}
