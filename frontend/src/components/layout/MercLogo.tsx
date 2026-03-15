import { cn } from '@/lib/utils'

interface MercLogoProps {
  /** 'nav' — compact single-line wordmark for the header
   *  'full' — card with catchphrase band, used on landing / standalone
   */
  variant?: 'nav' | 'full'
  className?: string
}

/**
 * Official MERC wordmark.
 *
 * Colors mirror the source design file:
 *   #0d1f3c — dark navy  (Medical / Estate)
 *   #1a5fa8 — brand blue (Real)
 *   #2d9cdb — sky        (Calculator™)
 *
 * Fonts Bebas Neue + Montserrat are already loaded globally via @fontsource.
 */
export default function MercLogo({ variant = 'nav', className }: MercLogoProps) {
  if (variant === 'nav') {
    return (
      <div className={cn('inline-flex select-none flex-col leading-none', className)}>
        {/* Line 1 */}
        <div className="flex items-baseline gap-[5px]">
          <span
            style={{ fontFamily: '"Bebas Neue", sans-serif', color: '#ffffff', letterSpacing: '2px' }}
            className="text-[26px]"
          >
            Medical
          </span>
          <span
            style={{ fontFamily: '"Bebas Neue", sans-serif', color: '#2d9cdb', letterSpacing: '2px' }}
            className="text-[26px]"
          >
            Real
          </span>
        </div>
        {/* Line 2 */}
        <div className="flex items-baseline gap-[5px]" style={{ marginTop: '-3px' }}>
          <span
            style={{ fontFamily: '"Bebas Neue", sans-serif', color: '#ffffff', letterSpacing: '2px' }}
            className="text-[26px]"
          >
            Estate
          </span>
          <span
            style={{ fontFamily: '"Bebas Neue", sans-serif', color: '#2d9cdb', letterSpacing: '2px' }}
            className="text-[16px] self-end pb-[3px]"
          >
            Calculator
            <sup
              style={{ fontFamily: 'Montserrat, sans-serif', fontSize: '8px', fontWeight: 600, color: '#2d9cdb' }}
            >
              ™
            </sup>
          </span>
        </div>
      </div>
    )
  }

  // Full card variant
  return (
    <div
      className={cn('inline-flex select-none flex-col', className)}
      style={{
        background: '#ffffff',
        boxShadow: '0 16px 64px rgba(13,31,60,0.13), 0 2px 8px rgba(13,31,60,0.07)',
        position: 'relative',
      }}
    >
      {/* Top gradient accent bar */}
      <div
        style={{
          height: '5px',
          background: 'linear-gradient(90deg, #0d3d6e 0%, #1a5fa8 40%, #2d9cdb 60%, #1a5fa8 80%, #0d3d6e 100%)',
        }}
      />

      {/* Wordmark */}
      <div style={{ padding: '32px 48px 16px 48px' }}>
        <div className="flex items-baseline gap-[10px]">
          <span style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '64px', letterSpacing: '4px', color: '#0d1f3c', lineHeight: 1 }}>
            Medical
          </span>
          <span style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '64px', letterSpacing: '4px', color: '#1a5fa8', lineHeight: 1 }}>
            Real
          </span>
        </div>
        <div className="flex items-baseline gap-[10px]" style={{ marginTop: '-4px' }}>
          <span style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '64px', letterSpacing: '4px', color: '#0d1f3c', lineHeight: 1 }}>
            Estate
          </span>
          <span style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '36px', letterSpacing: '4px', color: '#2d9cdb', lineHeight: 1, alignSelf: 'flex-end', paddingBottom: '6px' }}>
            Calculator
            <sup style={{ fontFamily: 'Montserrat, sans-serif', fontSize: '11px', fontWeight: 600, color: '#2d9cdb' }}>™</sup>
          </span>
        </div>
      </div>

      {/* Catchphrase band */}
      <div
        style={{
          borderTop: '1px solid #dce8f0',
          background: '#f0f5fa',
          padding: '10px 48px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <div style={{ width: '3px', height: '20px', background: 'linear-gradient(180deg, #2d9cdb, #1a5fa8)', borderRadius: '2px', flexShrink: 0 }} />
        <span style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '18px', letterSpacing: '5px', color: '#1a4a78', whiteSpace: 'nowrap' }}>
          <span style={{ color: '#1a5fa8' }}>Clinical Demand.</span> Precise Locations.
        </span>
      </div>

      {/* Footer strip */}
      <div
        style={{
          borderTop: '1px solid #dce8f0',
          padding: '8px 48px 10px 48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <span style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '13px', letterSpacing: '3px', color: '#94a9be' }}>
          25 Years · Fiduciary for Doctors
        </span>
        <span style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '13px', letterSpacing: '3px', color: '#1a5fa8' }}>
          CPT<span style={{ color: '#cbd6e2', margin: '0 4px' }}>·</span>DRG<span style={{ color: '#cbd6e2', margin: '0 4px' }}>·</span>ICD-10
        </span>
      </div>
    </div>
  )
}
