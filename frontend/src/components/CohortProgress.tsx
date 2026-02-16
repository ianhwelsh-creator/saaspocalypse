import type { CohortDetail } from '../types'

const ZONE_PILL: Record<string, { bg: string; text: string }> = {
  fortress: { bg: 'bg-[#e8f5ec]', text: 'text-[#1a9d3f]' },
  adaptation: { bg: 'bg-[#e8f0fa]', text: 'text-[#2b7fd4]' },
  compression: { bg: 'bg-[#faf3e0]', text: 'text-[#d49b1a]' },
  dead: { bg: 'bg-[#fae8e8]', text: 'text-[#d63939]' },
}

interface Props {
  cohort: CohortDetail
}

export default function CohortProgress({ cohort }: Props) {
  const pct = cohort.total_companies > 0
    ? Math.round((cohort.completed_companies / cohort.total_companies) * 100)
    : 0

  return (
    <div className="bg-surface-secondary rounded-xl border border-arena-border p-6">
      <h3 className="text-[15px] font-semibold text-arena-text mb-4">
        Analysis Progress
      </h3>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[12px] text-arena-muted">
            {cohort.completed_companies} of {cohort.total_companies} companies
          </span>
          <span className="text-[12px] font-medium text-arena-text-secondary">{pct}%</span>
        </div>
        <div className="w-full bg-arena-border-medium rounded-full h-2">
          <div
            className="bg-arena-link h-2 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Current company being analyzed */}
      {cohort.status === 'analyzing' && cohort.current_company && (
        <div className="flex items-center gap-2 text-[13px] text-arena-text-secondary mt-4 mb-4">
          <span className="w-2 h-2 rounded-full bg-arena-link animate-pulse flex-shrink-0" />
          <span>
            Analyzing <strong className="text-arena-text">{cohort.current_company}</strong>
            <span className="text-arena-muted ml-1">
              ({cohort.completed_companies + 1} of {cohort.total_companies})
            </span>
          </span>
        </div>
      )}

      {cohort.status === 'complete' && (
        <div className="flex items-center gap-2 text-[13px] text-arena-positive mt-4 mb-4">
          <span className="text-[16px]">✓</span>
          Analysis complete
        </div>
      )}

      {cohort.status === 'error' && (
        <div className="flex items-center gap-2 text-[13px] text-arena-negative mt-4 mb-4">
          <span className="text-[16px]">✗</span>
          Analysis encountered an error
        </div>
      )}

      {/* Completed companies as pill chips */}
      {cohort.members.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {cohort.members.map((m) => {
            const pill = ZONE_PILL[m.zone] || ZONE_PILL.dead
            return (
              <span
                key={m.evaluation_id}
                className={`text-[11px] font-medium px-2.5 py-1 rounded-md ${pill.bg} ${pill.text}`}
              >
                {m.company_name}
              </span>
            )
          })}
        </div>
      )}
    </div>
  )
}
