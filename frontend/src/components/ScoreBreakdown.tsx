import type { ScoreFactors } from '../types'

const X_FACTOR_LABELS: Record<string, string> = {
  regulatory_overlay: 'Regulatory Overlay',
  multi_stakeholder: 'Multi-Stakeholder',
  judgment_intensity: 'Judgment Intensity',
  process_depth: 'Process Depth',
  institutional_knowledge: 'Institutional Knowledge',
}

const Y_FACTOR_LABELS: Record<string, string> = {
  regulatory_lock_in: 'Regulatory Lock-in',
  data_gravity: 'Data Gravity',
  network_effects: 'Network Effects',
  portability_resistance: 'Portability Resistance',
  proprietary_enrichment: 'Proprietary Enrichment',
}

const X_COLORS = [
  '#3b82f6', // blue-500
  '#6366f1', // indigo-500
  '#8b5cf6', // violet-500
  '#a855f7', // purple-500
  '#c084fc', // purple-400
]

const Y_COLORS = [
  '#10b981', // emerald-500
  '#14b8a6', // teal-500
  '#06b6d4', // cyan-500
  '#0ea5e9', // sky-500
  '#38bdf8', // sky-400
]

interface Props {
  scoreFactors: ScoreFactors
  compact?: boolean
}

function FactorBar({
  label,
  value,
  max,
  color,
}: {
  label: string
  value: number
  max: number
  color: string
}) {
  const pct = (value / max) * 100
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] text-arena-muted w-[130px] shrink-0 text-right truncate">
        {label}
      </span>
      <div className="flex-1 h-[14px] bg-arena-border-medium/40 rounded-full overflow-hidden relative">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span
        className="text-[11px] font-mono font-semibold w-[28px] text-right shrink-0"
        style={{ color }}
      >
        {value}
      </span>
    </div>
  )
}

export default function ScoreBreakdown({ scoreFactors, compact }: Props) {
  const { x_factors, y_factors } = scoreFactors

  const xKeys = Object.keys(X_FACTOR_LABELS) as (keyof typeof X_FACTOR_LABELS)[]
  const yKeys = Object.keys(Y_FACTOR_LABELS) as (keyof typeof Y_FACTOR_LABELS)[]

  return (
    <div className={`space-y-4 ${compact ? 'mt-2' : 'mt-4'}`}>
      {/* Complexity sub-factors */}
      <div>
        <h5 className="text-[11px] font-semibold text-arena-text-secondary uppercase tracking-wider mb-2">
          Complexity Breakdown
        </h5>
        <div className="space-y-1.5">
          {xKeys.map((key, i) => (
            <FactorBar
              key={key}
              label={X_FACTOR_LABELS[key]}
              value={(x_factors as Record<string, number>)[key] ?? 0}
              max={20}
              color={X_COLORS[i]}
            />
          ))}
        </div>
      </div>

      {/* Data Moat sub-factors */}
      <div>
        <h5 className="text-[11px] font-semibold text-arena-text-secondary uppercase tracking-wider mb-2">
          Data Moat Breakdown
        </h5>
        <div className="space-y-1.5">
          {yKeys.map((key, i) => (
            <FactorBar
              key={key}
              label={Y_FACTOR_LABELS[key]}
              value={(y_factors as Record<string, number>)[key] ?? 0}
              max={20}
              color={Y_COLORS[i]}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
