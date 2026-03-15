import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ArrowRight, PlayCircle } from 'lucide-react'

export default function Hero() {
  const navigate = useNavigate()

  const scrollToHowItWorks = () => {
    const el = document.getElementById('how-it-works')
    if (el) {
      const top = el.getBoundingClientRect().top + window.scrollY - 80
      window.scrollTo({ top, behavior: 'smooth' })
    }
  }

  return (
    <section className="flex min-h-[calc(100vh-80px)] items-center bg-[hsl(215_63%_14%)] px-6 py-20">
      <div className="mx-auto max-w-[1280px] text-center">
        <h1 className="font-[family-name:var(--font-heading)] text-5xl leading-tight tracking-wide text-white md:text-7xl">
          UNDERSTAND HOW YOUR PRACTICE COMPARES —{' '}
          <span className="text-[hsl(204_66%_52%)]">AND GROW REVENUE</span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-white/70 md:text-lg">
          Compare with providers within your radius, uncover high-revenue procedures, and align
          with local demographics — all delivered in a comprehensive PDF report.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button
            size="lg"
            onClick={() => navigate('/buy')}
            className="h-12 gap-2 bg-[hsl(204_66%_52%)] px-8 text-base font-bold uppercase tracking-wide text-white hover:bg-[hsl(204_66%_45%)]"
          >
            Get My Comprehensive Report
            <ArrowRight size={18} />
          </Button>

          <Button
            variant="outline"
            size="lg"
            onClick={scrollToHowItWorks}
            className="h-12 gap-2 border-white/40 bg-transparent px-8 text-base font-medium text-white hover:bg-white/10 hover:text-white"
          >
            <PlayCircle size={18} />
            See How It Works
          </Button>
        </div>

        {/* Trust micro-copy */}
        <p className="mt-8 text-xs text-white/40">
          Healthcare-focused analytics · US provider data · Delivered within 5 business days
        </p>
      </div>
    </section>
  )
}
