import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ArrowRight, FileText } from 'lucide-react'

export default function ReportPreview() {
  const navigate = useNavigate()

  return (
    <section className="overflow-hidden bg-[hsl(217_33%_17%)] px-6 py-24">
      <div className="mx-auto max-w-[1280px]">
        {/* Heading */}
        <div className="mb-4 text-center">
          <span className="inline-flex items-center gap-2 rounded-full bg-[hsl(204_66%_52%/0.15)] px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-[hsl(204_66%_52%)]">
            <FileText size={12} />
            Sample Report
          </span>
          <h2 className="mt-4 font-[family-name:var(--font-heading)] text-4xl tracking-wide text-white md:text-5xl">
            SEE WHAT YOU&apos;LL RECEIVE
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-white/60">
            A professional competitive intelligence report with clinical demand analysis,
            procedure benchmarks, and demographic insights — tailored to your practice.
          </p>
        </div>

        {/* Report mockup — three tilted pages */}
        <div
          className="relative mx-auto mt-16 flex items-center justify-center"
          style={{ height: '520px', perspective: '1400px' }}
        >
          {/* Back-left page */}
          <div
            className="absolute"
            style={{
              transformOrigin: 'center center',
              transform: 'rotateY(22deg) rotateX(4deg) translateX(-260px) translateZ(-60px) scale(0.88)',
              boxShadow: '0 40px 100px rgba(13,31,60,0.6)',
              borderRadius: '8px',
              overflow: 'hidden',
              width: '360px',
              height: '480px',
              opacity: 0.55,
              pointerEvents: 'none',
            }}
          >
            <iframe
              src="/report-preview.html"
              title="Report preview (back)"
              style={{
                width: '900px',
                height: '1200px',
                border: 'none',
                transform: 'scale(0.4)',
                transformOrigin: 'top left',
                pointerEvents: 'none',
              }}
              scrolling="no"
            />
          </div>

          {/* Back-right page */}
          <div
            className="absolute"
            style={{
              transformOrigin: 'center center',
              transform: 'rotateY(-22deg) rotateX(4deg) translateX(260px) translateZ(-60px) scale(0.88)',
              boxShadow: '0 40px 100px rgba(13,31,60,0.6)',
              borderRadius: '8px',
              overflow: 'hidden',
              width: '360px',
              height: '480px',
              opacity: 0.55,
              pointerEvents: 'none',
            }}
          >
            <iframe
              src="/report-preview.html"
              title="Report preview (back right)"
              style={{
                width: '900px',
                height: '1200px',
                border: 'none',
                transform: 'scale(0.4)',
                transformOrigin: 'top left',
                pointerEvents: 'none',
              }}
              scrolling="no"
            />
          </div>

          {/* Front / center page — main */}
          <div
            className="absolute z-10"
            style={{
              transformOrigin: 'center center',
              transform: 'rotateX(5deg) rotateY(-4deg) translateZ(0px)',
              boxShadow: '0 60px 120px rgba(13,31,60,0.75), 0 0 0 1px rgba(255,255,255,0.06)',
              borderRadius: '10px',
              overflow: 'hidden',
              width: '440px',
              height: '480px',
              pointerEvents: 'none',
            }}
          >
            <iframe
              src="/report-preview.html"
              title="Report preview"
              style={{
                width: '900px',
                height: '1180px',
                border: 'none',
                transform: 'scale(0.489)',
                transformOrigin: 'top left',
                pointerEvents: 'none',
              }}
              scrolling="no"
            />
            {/* Gradient fade at bottom to soften clip */}
            <div
              className="pointer-events-none absolute bottom-0 left-0 right-0"
              style={{
                height: '120px',
                background: 'linear-gradient(to bottom, transparent, hsl(217 33% 17%))',
              }}
            />
          </div>
        </div>

        {/* CTA below the preview */}
        <div className="mt-12 text-center">
          <Button
            size="lg"
            onClick={() => navigate('/buy')}
            className="h-12 gap-2 bg-[hsl(204_66%_52%)] px-8 text-base font-bold uppercase tracking-wide text-white hover:bg-[hsl(204_66%_45%)]"
          >
            Get Your Comprehensive Report
            <ArrowRight size={18} />
          </Button>
          <p className="mt-3 text-xs text-white/35">
            Delivered as a PDF · Unique to your practice · Data from CMS &amp; NPPES
          </p>
        </div>
      </div>
    </section>
  )
}
