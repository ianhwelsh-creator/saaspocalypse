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
}

interface Props {
  summaries: BasketSummary[]
}

export default function BasketLegend({ summaries }: Props) {
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
                  <span
                    key={ticker}
                    className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-surface-raised text-arena-text-secondary"
                  >
                    {ticker}
                  </span>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
