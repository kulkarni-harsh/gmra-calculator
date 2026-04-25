import MercLogo from '@/components/layout/MercLogo'

export default function Footer() {
  return (
    <footer className="border-t-[3px] border-mcrec-blue bg-[#111B2E] px-5 py-9 md:px-14">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-6">
        <MercLogo variant="footer" />
        <div className="text-right text-[11px] leading-[1.9] text-mcrec-gray2">
          MCREC Reports LLC
          <br />
          <a href="mailto:reports@medrecalc.com" className="text-mcrec-teal hover:underline">
            reports@medrecalc.com
          </a>{' '}
          ·{' '}
          <a href="tel:+18884772241" className="text-mcrec-teal hover:underline">
            1-888-477-2241
          </a>
          <br />
          <a
            href="https://www.medicalrealestatecalculator.com"
            className="text-mcrec-teal hover:underline"
          >
            medicalrealestatecalculator.com
          </a>
          <br />
          <span className="text-[10px] text-white/30">
            Globe Medical Realty Advisors ·{' '}
            <a href="https://www.globemedllc.com" className="text-white/30 hover:underline">
              globemedllc.com
            </a>
          </span>
        </div>
      </div>

      <div className="mb-1.5 text-[10px] leading-[1.6] text-white/30">
        Reports operated by MCREC Reports LLC · Data powered by AlphaSophia · Patent and
        intellectual property owned by MCREC LLC
        <br />
        MCREC LLC is managing partner for MCREC Reports LLC
      </div>

      <div className="mb-4 text-[10px] tracking-wide text-white/25">
        CPT · DRG · ICD-10 &nbsp;|&nbsp; Patent Pending · Trademark Registered &nbsp;|&nbsp; 25
        Years · Fiduciary for Independent Physicians
      </div>

      <div className="text-[10px] leading-[1.6] text-white/20">
        © 2026 MCREC Reports LLC. All rights reserved. Medical Real Estate Calculator™ is a
        trademark of MCREC LLC.
      </div>

      <div className="mt-3 max-w-[800px] text-[9px] leading-[1.6] text-white/15">
        CPT® codes and descriptions are copyright 2026 American Medical Association. All rights
        reserved. CPT® is a registered trademark of the American Medical Association. Fee
        schedules, relative value units, conversion factors and/or related components are not
        assigned by the AMA, are not part of CPT, and the AMA is not recommending their use. The
        AMA does not directly or indirectly practice medicine or dispense medical services. The AMA
        assumes no liability for data contained or not contained herein.
      </div>
    </footer>
  )
}
