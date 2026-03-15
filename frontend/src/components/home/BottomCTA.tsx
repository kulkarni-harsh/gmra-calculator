import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

export default function BottomCTA() {
  const navigate = useNavigate()

  return (
    <section className="bg-[hsl(215_63%_14%)] px-6 py-20 text-center">
      <div className="mx-auto max-w-[1280px]">
        <h2 className="font-[family-name:var(--font-heading)] text-4xl tracking-wide text-white md:text-5xl">
          READY TO OUTGROW YOUR COMPETITION?
        </h2>
        <p className="mt-4 text-white/70">
          Includes a full competitive analysis, procedure benchmarks, and a comprehensive PDF report.
        </p>
        <Button
          size="lg"
          onClick={() => navigate('/buy')}
          className="mt-8 h-14 gap-2 bg-[hsl(204_66%_52%)] px-10 text-base font-bold uppercase tracking-wide text-white hover:bg-[hsl(204_66%_45%)]"
        >
          Get Your Comprehensive Report
          <ArrowRight size={18} />
        </Button>
      </div>
    </section>
  )
}
