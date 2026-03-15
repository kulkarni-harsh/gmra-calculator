import { Link } from 'react-router-dom'
import MercLogo from '@/components/layout/MercLogo'

export default function Footer() {
  return (
    <footer className="bg-[hsl(215_63%_14%)] text-white/70">
      <div className="mx-auto max-w-[1280px] px-6 py-14">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-3">

          {/* Brand column */}
          <div className="space-y-4">
            <MercLogo variant="nav" />
            <p className="text-sm leading-relaxed text-white/55">
              Competitive intelligence reports for medical practices.
              Understand your market, grow your revenue.
            </p>

            {/* GMRA parent company — white bg pill so PNG logo reads on dark bg */}
            <div className="mt-4 flex items-center gap-3">
              <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30 whitespace-nowrap">
                A service of
              </span>
              <a href="https://www.globemedllc.com/" target="_blank" rel="noopener noreferrer" className="overflow-hidden rounded-xl bg-white block hover:opacity-85 transition-opacity">
                <img
                  src="/gmra_logo.png"
                  alt="Globe Medical Realty Advisors"
                  className="h-10 w-auto object-contain"
                />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-white">
              Quick Links
            </h3>
            <ul className="space-y-2.5 text-sm">
              <li>
                <Link to="/" className="transition-colors hover:text-white">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/buy" className="transition-colors hover:text-white">
                  Buy / Book Consultation
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-white">
              Legal
            </h3>
            <ul className="space-y-2.5 text-sm">
              <li>
                <a href="#" className="transition-colors hover:text-white">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#" className="transition-colors hover:text-white">
                  Terms of Service
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-white/10 pt-6 sm:flex-row">
          <p className="text-xs text-white/35">
            © 2026 Medical Real Estate Calculator™. All rights reserved.
          </p>
          <a
            href="https://www.globemedllc.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-white/25 transition-colors hover:text-white/50"
          >
            Powered by Globe Medical Realty Advisors
          </a>
        </div>
      </div>
    </footer>
  )
}
