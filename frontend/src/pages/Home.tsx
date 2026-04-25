import Hero from '@/components/home/Hero'
import AmberBand from '@/components/layout/AmberBand'
import IndependenceBar from '@/components/layout/IndependenceBar'
import WhatItIs from '@/components/home/WhatItIs'
import SiteNeutrality from '@/components/home/SiteNeutrality'
import WhoItsFor from '@/components/home/WhoItsFor'
import ReportsPricing from '@/components/home/ReportsPricing'
import CalculatorVsGlobe from '@/components/home/CalculatorVsGlobe'
import AboutGlobe from '@/components/home/AboutGlobe'
import FaqSection from '@/components/home/FaqSection'
import CtaSection from '@/components/home/CtaSection'

export default function Home() {
  return (
    <>
      <Hero />
      <AmberBand />
      <IndependenceBar />
      <WhatItIs />
      <SiteNeutrality />
      <WhoItsFor />
      <ReportsPricing />
      <CalculatorVsGlobe />
      <AboutGlobe />
      <FaqSection />
      <CtaSection />
    </>
  )
}
