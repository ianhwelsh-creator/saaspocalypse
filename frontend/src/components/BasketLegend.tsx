import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import type { BasketSummary } from '../types'

const ZONE_META: Record<string, { tagline: string; axis: string }> = {
  dead_zone: {
    tagline: 'Existential AI risk',
    axis: 'Simple workflows · Shallow data moat',
  },
  compression_zone: {
    tagline: 'Revenue compression from AI',
    axis: 'Simple workflows · Deep data moat',
  },
  adaptation_zone: {
    tagline: 'Must embed AI faster than competition',
    axis: 'Complex workflows · Shallow data moat',
  },
  fortress_zone: {
    tagline: 'AI strengthens their position',
    axis: 'Complex workflows · Deep data moat',
  },
  ai_etfs: {
    tagline: 'AI-exposure benchmark',
    axis: 'Equity ETFs for comparison',
  },
  sp500: {
    tagline: 'Broad market benchmark',
    axis: 'S&P 500 index (SPY)',
  },
}

interface Props {
  summaries: BasketSummary[]
  tickerRationale?: Record<string, string[]>
  tickerChanges?: Record<string, number>
}

function TickerChip({
  ticker,
  bullets,
  zoneColor,
  changePct,
}: {
  ticker: string
  bullets?: string[]
  zoneColor: string
  changePct?: number
}) {
  const [show, setShow] = useState(false)
  const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({})
  const chipRef = useRef<HTMLSpanElement>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [])

  const handleEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    if (chipRef.current) {
      const rect = chipRef.current.getBoundingClientRect()
      const spaceBelow = window.innerHeight - rect.bottom
      const goUp = spaceBelow < 200

      // Center horizontally on the chip, clamp to viewport edges
      const tooltipWidth = 272
      let left = rect.left + rect.width / 2 - tooltipWidth / 2
      left = Math.max(8, Math.min(left, window.innerWidth - tooltipWidth - 8))

      setTooltipStyle({
        position: 'fixed',
        left,
        width: tooltipWidth,
        ...(goUp
          ? { bottom: window.innerHeight - rect.top + 8 }
          : { top: rect.bottom + 8 }),
        zIndex: 9999,
      })
    }
    setShow(true)
  }

  const handleLeave = () => {
    timeoutRef.current = setTimeout(() => setShow(false), 150)
  }

  if (!bullets?.length) {
    return (
      <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-surface-raised text-arena-text-secondary">
        {ticker}
      </span>
    )
  }

  const hasChange = changePct !== undefined && changePct !== null
  const isPositive = hasChange && changePct >= 0

  return (
    <span
      ref={chipRef}
      className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-surface-raised text-arena-text-secondary cursor-pointer hover:bg-surface-raised/80 transition-colors"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      {ticker}
      {show &&
        createPortal(
          <div
            style={tooltipStyle}
            onMouseEnter={() => {
              if (timeoutRef.current) clearTimeout(timeoutRef.current)
            }}
            onMouseLeave={handleLeave}
          >
            <div className="rounded-lg border border-arena-border bg-surface-primary shadow-xl p-3">
              {/* Header — ticker + performance badge */}
              <div className="flex items-center justify-between mb-2">
                <span
                  className="text-[12px] font-bold font-mono"
                  style={{ color: zoneColor }}
                >
                  {ticker}
                </span>
                {hasChange && (
                  <span
                    className={`text-[11px] font-mono font-semibold px-2 py-0.5 rounded-md ${
                      isPositive
                        ? 'bg-arena-positive/10 text-arena-positive'
                        : 'bg-arena-negative/10 text-arena-negative'
                    }`}
                  >
                    {isPositive ? '+' : ''}{changePct.toFixed(1)}%
                  </span>
                )}
              </div>
              {/* Bullet list */}
              <ul className="space-y-1.5">
                {bullets.map((bullet, i) => (
                  <li key={i} className="flex gap-2 text-[11px] text-arena-text-secondary leading-relaxed">
                    <span className="text-arena-muted mt-0.5 flex-shrink-0">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>,
          document.body,
        )}
    </span>
  )
}

export default function BasketLegend({ summaries, tickerRationale, tickerChanges }: Props) {
  if (!summaries?.length) return null

  return (
    <div className="px-6 pb-6">
      <div className="grid grid-cols-2 gap-3">
        {summaries.map((s) => {
          const meta = ZONE_META[s.zone]
          return (
            <div
              key={s.zone}
              className="relative rounded-lg border border-arena-border bg-surface-secondary/50 px-4 py-3 overflow-hidden"
            >
              {/* Color accent bar */}
              <div
                className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-lg"
                style={{ backgroundColor: s.color }}
              />

              {/* Zone name + change */}
              <div className="flex items-center justify-between mb-1.5">
                <span
                  className="text-[12px] font-semibold"
                  style={{ color: s.color }}
                >
                  {s.label}
                </span>
                <span
                  className={`text-[11px] font-mono px-2 py-0.5 rounded-md ${
                    s.change_from_baseline >= 0
                      ? 'bg-arena-positive/10 text-arena-positive'
                      : 'bg-arena-negative/10 text-arena-negative'
                  }`}
                >
                  {s.change_from_baseline >= 0 ? '+' : ''}
                  {s.change_from_baseline.toFixed(1)}%
                </span>
              </div>

              {/* Tagline */}
              {meta && (
                <p className="text-[11px] text-arena-text-tertiary leading-relaxed mb-1">
                  {meta.tagline}
                </p>
              )}

              {/* Axis */}
              {meta && (
                <p className="text-[10px] text-arena-muted mb-2.5">
                  {meta.axis}
                </p>
              )}

              {/* Tickers */}
              <div className="flex flex-wrap gap-1.5">
                {s.tickers.map((ticker) => (
                  <TickerChip
                    key={ticker}
                    ticker={ticker}
                    bullets={tickerRationale?.[ticker]}
                    zoneColor={s.color}
                    changePct={tickerChanges?.[ticker]}
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
