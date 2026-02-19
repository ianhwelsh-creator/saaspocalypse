import { NavLink } from 'react-router-dom'
import { ReactNode } from 'react'

/* ── Nav icons (Lucide-style, 18×18) ──────────────────────────────────────── */

function DashboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  )
}

function EvaluatorIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
      <path d="M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12z" />
      <path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" />
    </svg>
  )
}

function CohortsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  )
}

function WatchlistIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function NewsletterIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  )
}

const navItems = [
  { to: '/', label: 'Dashboard', Icon: DashboardIcon },
  { to: '/evaluator', label: 'Evaluator', Icon: EvaluatorIcon },
  { to: '/cohorts', label: 'Cohorts', Icon: CohortsIcon },
  { to: '/watchlist', label: 'Watchlist', Icon: WatchlistIcon },
  { to: '/newsletter', label: 'Newsletter', Icon: NewsletterIcon },
]

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-surface-primary">
      {/* Top ribbon */}
      <header className="flex items-center justify-between px-5 h-[52px] border-b border-arena-border bg-surface-secondary flex-shrink-0">
        {/* Left — logo + nav */}
        <div className="flex items-center gap-7">
          {/* Logo mark + name */}
          <NavLink to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#1a9d3f] to-[#16833a] flex items-center justify-center shadow-sm">
              <svg className="w-[18px] h-[18px] text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 3v18h18" />
                <path d="m7 17 4-8 4 4 5-10" />
              </svg>
            </div>
            <span className="text-[15px] font-bold text-[#1a9d3f] tracking-tight">
              SaaSpocalypse
            </span>
          </NavLink>

          {/* Divider */}
          <div className="w-px h-6 bg-arena-border" />

          {/* Nav links */}
          <nav className="flex items-center gap-0.5">
            {navItems.map(({ to, label, Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all ${
                    isActive
                      ? 'bg-[#1a9d3f]/8 text-[#1a9d3f]'
                      : 'text-arena-muted hover:text-arena-text hover:bg-surface-tertiary/60'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon className={`w-[16px] h-[16px] ${isActive ? 'text-[#1a9d3f]' : ''}`} />
                    {label}
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Right — search + live */}
        <div className="flex items-center gap-3">
          {/* Live badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#1a9d3f]/8">
            <span className="w-1.5 h-1.5 rounded-full bg-[#1a9d3f] animate-pulse" />
            <span className="text-[11px] font-medium text-[#1a9d3f]">Live</span>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 overflow-y-auto bg-surface-primary">
        {children}
      </main>
    </div>
  )
}
