import { useState, useEffect } from 'react'
import type { BasketSummary, StockDetail } from '../types'

function formatPrice(price: number): string {
  if (price === 0) return '—'
  return price.toFixed(2)
}

function formatChange(pct: number): string {
  if (pct === 0) return '0.00%'
  const sign = pct > 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

interface TickerGroup {
  zone: string
  label: string
  color: string
  stocks: StockDetail[]
}

interface Props {
  summaries: BasketSummary[]
}

export default function StockTicker({ summaries }: Props) {
  const [groups, setGroups] = useState<TickerGroup[]>([])

  useEffect(() => {
    if (!summaries || summaries.length === 0) return

    let cancelled = false

    const fetchAll = async () => {
      try {
        const results = await Promise.all(
          summaries.map(async (s) => {
            const res = await fetch(`/api/stocks/baskets/${s.zone}`)
            if (!res.ok) return { zone: s.zone, label: s.label, color: s.color, stocks: [] as StockDetail[] }
            const stocks: StockDetail[] = await res.json()
            return { zone: s.zone, label: s.label, color: s.color, stocks }
          })
        )
        if (!cancelled) setGroups(results)
      } catch {
        // Silently fail — ticker tape is non-critical
      }
    }

    fetchAll()
    const interval = setInterval(fetchAll, 900_000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [summaries])

  if (groups.length === 0 || groups.every((g) => g.stocks.length === 0)) return null

  const renderItems = (key: string) =>
    groups.map((group) => (
      <div key={`${key}-${group.zone}`} className="flex items-center gap-0.5 shrink-0">
        {/* Zone label */}
        <span
          className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded mr-1"
          style={{ color: group.color, backgroundColor: `${group.color}14` }}
        >
          {group.label}
        </span>
        {/* Tickers in this zone */}
        {group.stocks.map((t) => (
          <div
            key={`${key}-${t.ticker}`}
            className="flex items-center gap-1.5 px-2.5 py-1"
          >
            <span className="text-[12px] font-semibold text-arena-text font-mono">
              {t.ticker}
            </span>
            <span className="text-[11px] font-mono text-arena-text-secondary">
              {formatPrice(t.current_price)}
            </span>
            <span
              className="text-[11px] font-mono font-medium"
              style={{
                color: t.change_pct > 0 ? '#1a9d3f' : t.change_pct < 0 ? '#d63939' : '#9ca3af',
              }}
            >
              {formatChange(t.change_pct)}
            </span>
          </div>
        ))}
        {/* Separator between zones */}
        <span className="text-arena-muted mx-2 opacity-40">·</span>
      </div>
    ))

  return (
    <div className="border-b border-arena-border bg-surface-tertiary/50 overflow-hidden flex-shrink-0">
      <div className="ticker-scroll flex items-center whitespace-nowrap py-0.5">
        <div className="ticker-track flex items-center">
          {renderItems('a')}
        </div>
        <div className="ticker-track flex items-center" aria-hidden>
          {renderItems('b')}
        </div>
      </div>
    </div>
  )
}
