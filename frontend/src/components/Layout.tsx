import { NavLink } from 'react-router-dom'
import { ReactNode } from 'react'

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/evaluator', label: 'Evaluator' },
  { to: '/cohorts', label: 'Cohorts' },
  { to: '/watchlist', label: 'Watchlist' },
  { to: '/newsletter', label: 'Newsletter' },
]

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-surface-primary">
      {/* Top ribbon */}
      <header className="flex items-center justify-between px-6 h-12 border-b border-arena-border bg-surface-tertiary flex-shrink-0">
        {/* Left — logo + nav */}
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <h1 className="text-[15px] font-semibold text-arena-text tracking-tight">
              SaaSpocalypse
            </h1>
            <span className="text-[11px] text-arena-muted hidden sm:inline">
              AI Disruption Tracker
            </span>
          </div>

          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                    isActive
                      ? 'bg-surface-raised text-arena-text'
                      : 'text-arena-text-tertiary hover:text-arena-text hover:bg-surface-raised/50'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Right — live indicator */}
        <div className="flex items-center gap-2 text-[11px] text-arena-muted">
          <span className="w-1.5 h-1.5 rounded-full bg-arena-positive" />
          Live
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 overflow-y-auto bg-surface-primary">
        {children}
      </main>
    </div>
  )
}
