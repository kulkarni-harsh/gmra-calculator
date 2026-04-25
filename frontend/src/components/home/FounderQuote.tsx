export default function FounderQuote() {
  return (
    <div className="mt-9 flex flex-wrap items-center gap-9 rounded-sm bg-mcrec-navy p-9 md:p-14">
      <img
        src="/founder.jpg"
        alt="David Rutson, Founder of Globe Medical Realty Advisors — 25 years of physician-side fiduciary medical real estate representation"
        onError={(e) => {
          // Fall back to neutral placeholder if /founder.jpg is not yet uploaded.
          ;(e.currentTarget as HTMLImageElement).style.background = '#9BAAC4'
          ;(e.currentTarget as HTMLImageElement).style.visibility = 'hidden'
          const parent = e.currentTarget.parentElement
          if (parent && !parent.querySelector('.founder-fallback')) {
            const fallback = document.createElement('div')
            fallback.className =
              'founder-fallback h-40 w-40 shrink-0 rounded-full border-[3px] border-mcrec-blue bg-mcrec-gray2'
            parent.insertBefore(fallback, e.currentTarget)
          }
        }}
        className="h-40 w-40 shrink-0 rounded-full border-[3px] border-mcrec-blue object-cover"
      />
      <div className="min-w-[280px] flex-1">
        <p className="text-[15px] italic leading-[1.9] text-white/80">
          <span className="mr-1 align-[-16px] font-[family-name:var(--font-heading)] text-5xl leading-none text-mcrec-blue">
            "
          </span>
          Knowing the income-producing factors of a location is the most critical first step in any
          lease negotiation or renewal. We have always provided this to our clients. Now any
          independent practice can access it directly — no broker required.
        </p>
        <div className="mt-4 text-[11px] font-semibold tracking-wide text-mcrec-gray2">
          <strong className="block text-[13px] tracking-normal text-white">David Rutson</strong>
          Principal Advisor &amp; Founder, Globe Medical Realty Advisors · 25 Years · Fiduciary for
          Independent Physicians
        </div>
      </div>
    </div>
  )
}
