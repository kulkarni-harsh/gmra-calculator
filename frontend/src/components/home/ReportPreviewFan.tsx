import type { CSSProperties } from 'react'
import reportTemplateHtml from '../../assets/MREC_Report_TEMPLATE_T1.html?raw'

interface PreviewCard {
  id: string
  label: string
  accent: string
  scrollTop: number
  frameClassName: string
}

const PREVIEW_TEMPLATE = reportTemplateHtml.replace(
  'mapImageSrc: "./map_coords_TX_outdoors.png",',
  'mapImageSrc: null,',
)

const PREVIEWS: ReadonlyArray<PreviewCard> = [
  {
    id: 'top',
    label: 'Sample',
    accent: 'Top',
    scrollTop: 980,
    frameClassName:
      'md:absolute md:left-4 md:top-10 md:w-[250px] md:-rotate-[11deg] md:translate-y-6 lg:left-6 lg:w-[285px]',
  },
  {
    id: 'middle',
    label: 'Sample',
    accent: 'Mid',
    scrollTop: 0,
    frameClassName:
      'md:absolute md:left-1/2 md:top-0 md:z-20 md:w-[280px] md:-translate-x-1/2 lg:w-[320px]',
  },
  {
    id: 'bottom',
    label: 'Sample',
    accent: 'Lower',
    scrollTop: 980,
    frameClassName:
      'md:absolute md:right-4 md:top-10 md:w-[250px] md:rotate-[11deg] md:translate-y-7 lg:right-6 lg:w-[285px]',
  },
]

export default function ReportPreviewFan() {
  return (
    <div className="relative mx-auto w-full max-w-[660px]">
      <div className="relative grid gap-5 md:min-h-[430px] md:grid-cols-1">
        {PREVIEWS.map((preview) => (
          <div
            key={preview.id}
            className={`group relative mx-auto w-full max-w-[320px] overflow-hidden rounded-[24px] border border-white/14 bg-white/[0.06] shadow-[0_24px_90px_rgba(3,11,24,0.28)] backdrop-blur-sm md:max-w-none ${preview.frameClassName}`}
          >
            <div className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center justify-between px-4 py-3">
              <div className="rounded-full border border-white/15 bg-mcrec-navy/70 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[2.5px] text-white/82">
                {preview.label}
              </div>
            </div>

            <div className="relative h-[250px] md:h-[360px]">
              <iframe
                title={preview.label}
                srcDoc={PREVIEW_TEMPLATE}
                sandbox="allow-same-origin allow-scripts"
                scrolling="no"
                style={
                  {
                    '--preview-offset-mobile': `-${preview.scrollTop * 0.3}px`,
                    '--preview-offset-desktop': `-${preview.scrollTop * 0.4}px`,
                  } as CSSProperties
                }
                className="pointer-events-none absolute left-1/2 top-0 h-[2200px] w-[900px] -translate-x-1/2 translate-y-[var(--preview-offset-mobile)] origin-top-left scale-[0.3] border-0 blur-[3.2px] saturate-[0.88] md:left-0 md:translate-x-0 md:translate-y-[var(--preview-offset-desktop)] md:scale-[0.4]"
              />
              <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(13,31,60,0.12)_0%,rgba(13,31,60,0.04)_30%,rgba(255,255,255,0.02)_100%)]" />
              <div className="pointer-events-none absolute inset-0 ring-1 ring-inset ring-white/8" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
