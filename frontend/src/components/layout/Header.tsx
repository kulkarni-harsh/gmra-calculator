import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import MercLogo from '@/components/layout/MercLogo'

interface NavLink {
  hash: string
  label: string
}

const LINKS: ReadonlyArray<NavLink> = [
  { hash: 'what-it-is', label: 'What It Is' },
  { hash: 'who-its-for', label: "Who It's For" },
  { hash: 'site-neutrality', label: '2026 Opportunity' },
  { hash: 'reports', label: 'Reports & Pricing' },
  { hash: 'globe-mcrec', label: 'GMRA & MCREC' },
  { hash: 'faq', label: 'FAQs' },
]

export default function Header() {
  const { pathname, hash } = useLocation()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  // After arriving on `/` with a hash (e.g. via cross-route nav), scroll to the section.
  useEffect(() => {
    if (pathname !== '/' || !hash) return
    const id = hash.replace(/^#/, '')
    // Wait one frame so the target section has mounted.
    const raf = requestAnimationFrame(() => {
      const el = document.getElementById(id)
      if (el) {
        const y = el.getBoundingClientRect().top + window.scrollY - 72
        window.scrollTo({ top: y, behavior: 'smooth' })
      }
    })
    return () => cancelAnimationFrame(raf)
  }, [pathname, hash])

  const goToAnchor = (target: string) => {
    setMenuOpen(false)
    if (pathname === '/') {
      const el = document.getElementById(target)
      if (el) {
        const y = el.getBoundingClientRect().top + window.scrollY - 72
        window.scrollTo({ top: y, behavior: 'smooth' })
      }
    } else {
      navigate(`/#${target}`)
    }
  }

  return (
    <header className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-mcrec-light bg-white/95 px-5 backdrop-blur md:px-14">
      <Link to="/" className="hover:opacity-90" onClick={() => setMenuOpen(false)}>
        <MercLogo variant="nav" />
      </Link>

      <button
        className="md:hidden"
        onClick={() => setMenuOpen((v) => !v)}
        aria-label="Toggle menu"
      >
        {menuOpen ? <X size={22} className="text-mcrec-navy" /> : <Menu size={22} className="text-mcrec-navy" />}
      </button>

      <nav className="hidden items-center gap-1 md:flex">
        {LINKS.map((link) => (
          <button
            key={link.hash}
            onClick={() => goToAnchor(link.hash)}
            className="rounded-sm px-3.5 py-2 text-xs font-medium text-mcrec-gray transition-colors hover:text-mcrec-navy"
          >
            {link.label}
          </button>
        ))}
        <a
          href="tel:+18884772241"
          className="ml-2 mr-3 text-[11px] font-semibold tracking-wide text-mcrec-navy hover:text-mcrec-blue"
        >
          1-888-477-2241
        </a>
        <Link
          to="/buy"
          className="rounded-sm bg-mcrec-blue px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-white transition-colors hover:bg-mcrec-navy"
        >
          Order a Report
        </Link>
      </nav>

      {menuOpen && (
        <div className="absolute left-0 right-0 top-16 flex flex-col gap-1 border-b border-mcrec-light bg-white px-5 py-4 shadow-lg md:hidden">
          {LINKS.map((link) => (
            <button
              key={link.hash}
              onClick={() => goToAnchor(link.hash)}
              className="rounded-sm px-3 py-2 text-left text-sm font-medium text-mcrec-gray hover:bg-mcrec-off hover:text-mcrec-navy"
            >
              {link.label}
            </button>
          ))}
          <Link
            to="/buy"
            onClick={() => setMenuOpen(false)}
            className="mt-2 rounded-sm bg-mcrec-blue px-4 py-2.5 text-center text-xs font-semibold uppercase tracking-wide text-white"
          >
            Order a Report
          </Link>
        </div>
      )}
    </header>
  )
}
