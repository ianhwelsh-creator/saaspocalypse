import { useState } from 'react'
import type { ScoreFactors, QuestionDetail } from '../types'

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

// Question labels per subcategory
const X_QUESTION_LABELS: Record<string, string[]> = {
  regulatory_overlay: ['Legal Risk', 'Certification', 'Audit Trail', 'Agency Submission'],
  multi_stakeholder: ['Handoffs', 'Conflict Resolution', 'External Interaction', 'Segregation of Duties'],
  judgment_intensity: ['Deterministic Mapping', 'Tenure Impact', 'Unstructured Context', 'Exception Handling'],
  process_depth: ['Downstream Domino', 'Duration', 'Reversibility', 'Physical Consequence'],
  institutional_knowledge: ['Integration Cost', 'Custom Taxonomy', 'Training Time', 'Attrition Risk'],
}

const Y_QUESTION_LABELS: Record<string, string[]> = {
  regulatory_lock_in: ['Retention Rule', 'System of Record', 'Migration Risk', 'Data Sovereignty'],
  data_gravity: ['API Hub', 'Downstream Breakage', 'Single Source', 'Automated Ingestion'],
  network_effects: ['Cross-Pollination', 'Marketplace', 'Standardization', 'Benchmarking'],
  portability_resistance: ['Context Loss', 'Entanglement', 'Egress Friction', 'Proprietary Format'],
  proprietary_enrichment: ['Net-New Generation', 'Usage-Based ML', 'External Signals', 'Unscrapable'],
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

function QuestionScore({ value, max = 5 }: { value: number; max?: number }) {
  const dots = []
  for (let i = 0; i < max; i++) {
    dots.push(
      <div
        key={i}
        className={`w-[6px] h-[6px] rounded-full ${
          i < value ? 'bg-current' : 'bg-arena-border-medium/40'
        }`}
      />
    )
  }
  return (
    <div className="flex items-center gap-[2px]">
      {dots}
      <span className="text-[10px] font-mono ml-1 opacity-70">{value}</span>
    </div>
  )
}

function FactorBar({
  label,
  value,
  max,
  color,
  detail,
  questionLabels,
}: {
  label: string
  value: number
  max: number
  color: string
  detail?: QuestionDetail
  questionLabels?: string[]
}) {
  const [expanded, setExpanded] = useState(false)
  const pct = (value / max) * 100
  const hasDetail = detail && questionLabels

  return (
    <div>
      <div
        className={`flex items-center gap-2 ${hasDetail ? 'cursor-pointer hover:bg-white/5 -mx-1 px-1 rounded' : ''}`}
        onClick={() => hasDetail && setExpanded(!expanded)}
      >
        <span className="text-[11px] text-arena-muted w-[130px] shrink-0 text-right truncate flex items-center justify-end gap-1">
          {hasDetail && (
            <span className="text-[9px] opacity-50">{expanded ? '▼' : '▶'}</span>
          )}
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

      {/* Expanded question-level detail */}
      {expanded && hasDetail && (
        <div className="ml-[138px] mr-[36px] mt-1 mb-2 p-2 rounded-md bg-surface-raised/60 border border-arena-border-medium/30">
          <div className="text-[10px] font-mono text-arena-muted mb-1.5">{detail.math}</div>
          <div className="space-y-1">
            {questionLabels.map((qLabel, qi) => {
              const qKey = `q${qi + 1}` as keyof QuestionDetail
              const qVal = detail[qKey] as number
              return (
                <div key={qi} className="flex items-center gap-2">
                  <span className="text-[10px] text-arena-muted w-[120px] shrink-0 truncate">
                    Q{qi + 1}: {qLabel}
                  </span>
                  <div style={{ color }} className="flex items-center">
                    <QuestionScore value={qVal} />
                  </div>
                </div>
              )
            })}
          </div>
          {detail.rationale && (
            <p className="text-[10px] text-arena-text-secondary mt-1.5 leading-relaxed italic">
              {detail.rationale}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default function ScoreBreakdown({ scoreFactors, compact }: Props) {
  const { x_factors, y_factors, x_detail, y_detail, investment_sentiment } = scoreFactors

  const xKeys = Object.keys(X_FACTOR_LABELS) as (keyof typeof X_FACTOR_LABELS)[]
  const yKeys = Object.keys(Y_FACTOR_LABELS) as (keyof typeof Y_FACTOR_LABELS)[]

  const hasDetail = !!(x_detail || y_detail)

  return (
    <div className={`space-y-4 ${compact ? 'mt-2' : 'mt-4'}`}>
      {/* Investment Sentiment badge */}
      {investment_sentiment && (
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold text-arena-text-secondary uppercase tracking-wider">
            AI Impact Sentiment:
          </span>
          <span
            className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
              investment_sentiment === 'Buy'
                ? 'bg-emerald-500/20 text-emerald-400'
                : investment_sentiment === 'Sell'
                ? 'bg-red-500/20 text-red-400'
                : 'bg-amber-500/20 text-amber-400'
            }`}
          >
            {investment_sentiment}
          </span>
        </div>
      )}

      {hasDetail && (
        <p className="text-[10px] text-arena-muted italic">
          Click any subcategory to see question-level scoring detail
        </p>
      )}

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
              detail={x_detail?.[key]}
              questionLabels={X_QUESTION_LABELS[key]}
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
              detail={y_detail?.[key]}
              questionLabels={Y_QUESTION_LABELS[key]}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
