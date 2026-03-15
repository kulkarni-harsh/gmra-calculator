import Hero from '@/components/home/Hero'
import ValuePillars from '@/components/home/ValuePillars'
import Deliverables from '@/components/home/Deliverables'
import ReportPreview from '@/components/home/ReportPreview'
import TrustBadges from '@/components/home/TrustBadges'
import BottomCTA from '@/components/home/BottomCTA'

export default function Home() {
  return (
    <>
      <Hero />
      <ValuePillars />
      <Deliverables />
      <ReportPreview />
      <TrustBadges />
      <BottomCTA />
    </>
  )
}
