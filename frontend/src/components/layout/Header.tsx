import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import MercLogo from '@/components/layout/MercLogo'

export default function Header() {
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const navLinks = [
    { to: '/', label: 'Home' },
    { to: '/buy', label: 'Buy / Book Consultation' },
  ]

  return (
    <header className="sticky top-0 z-50 w-full bg-[hsl(215_63%_14%)] shadow-md">
      <div className="mx-auto flex max-w-[1280px] items-center justify-between px-6 py-3">
        {/* Wordmark */}
        <Link to="/" className="hover:opacity-85 transition-opacity">
          <MercLogo variant="nav" />
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-2 md:flex">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                pathname === to
                  ? 'bg-white text-[hsl(215_63%_14%)]'
                  : 'text-white/80 hover:text-white'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Mobile hamburger */}
        <button
          className="text-white md:hidden"
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile drawer */}
      {menuOpen && (
        <nav className="border-t border-white/10 bg-[hsl(215_63%_14%)] px-6 pb-4 md:hidden">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setMenuOpen(false)}
              className={`block py-3 text-sm font-medium ${
                pathname === to ? 'text-[#2d9cdb]' : 'text-white/80'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  )
}
