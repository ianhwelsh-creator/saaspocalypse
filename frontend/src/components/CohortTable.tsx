import type { CohortMemberSummary } from '../types'

const ZONE_ORDER: Record<string, number> = {
  fortress: 0,
  adaptation: 1,
  compression: 2,
  dead: 3,
}

const ZONE_PILL: Record<string, { bg: string; text: string; label: string }> = {
  fortress: { bg: 'bg-[#e8f5ec]', text: 'text-[#1a9d3f]', label: 'Fortress' },
  adaptation: { bg: 'bg-[#e8f0fa]', text: 'text-[#2b7fd4]', label: 'Adaptation' },
  compression: { bg: 'bg-[#faf3e0]', text: 'text-[#d49b1a]', label: 'Compression' },
  dead: { bg: 'bg-[#fae8e8]', text: 'text-[#d63939]', label: 'Dead Zone' },
}

interface Props {
  members: CohortMemberSummary[]
  onSelectMember: (evaluationId: number) => void
  editMode?: boolean
  onRemoveMember?: (evaluationId: number) => void
  pendingRemovals?: Set<number>
}

export default function CohortTable({ members, onSelectMember, editMode, onRemoveMember, pendingRemovals }: Props) {
  const sorted = [...members].sort((a, b) => {
    const oa = ZONE_ORDER[a.zone] ?? 99
    const ob = ZONE_ORDER[b.zone] ?? 99
    return oa - ob
  })

  return (
    <div className="bg-surface-secondary rounded-xl border border-arena-border overflow-hidden">
      <div className="px-6 pt-5 pb-3">
        <h3 className="text-[15px] font-semibold text-arena-text">
          Cohort Summary
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-arena-border">
              {editMode && <th className="pl-4 pr-1 py-2.5 w-8"></th>}
              <th className="px-6 py-2.5 text-[11px] font-medium text-arena-muted uppercase tracking-wide">Company</th>
              <th className="px-4 py-2.5 text-[11px] font-medium text-arena-muted uppercase tracking-wide">Zone</th>
              <th className="px-4 py-2.5 text-[11px] font-medium text-arena-muted uppercase tracking-wide text-center">Complexity</th>
              <th className="px-4 py-2.5 text-[11px] font-medium text-arena-muted uppercase tracking-wide text-center">Data Moat</th>
              <th className="px-4 py-2.5 text-[11px] font-medium text-arena-muted uppercase tracking-wide">Key Risk</th>
              <th className="px-4 py-2.5 text-[11px] font-medium text-arena-muted uppercase tracking-wide">AI Summary</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((m) => {
              const pill = ZONE_PILL[m.zone] || ZONE_PILL.dead
              const isRemoved = pendingRemovals?.has(m.evaluation_id)
              return (
                <tr
                  key={m.evaluation_id}
                  onClick={() => !editMode && onSelectMember(m.evaluation_id)}
                  className={`border-b border-arena-border/50 transition-colors group ${
                    isRemoved
                      ? 'bg-[#fae8e8]/40'
                      : editMode
                        ? 'hover:bg-surface-tertiary/40'
                        : 'hover:bg-surface-tertiary/60 cursor-pointer'
                  }`}
                >
                  {editMode && (
                    <td className="pl-4 pr-1 py-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onRemoveMember?.(m.evaluation_id)
                        }}
                        className={`w-6 h-6 flex items-center justify-center rounded-md transition-colors ${
                          isRemoved
                            ? 'bg-[#d63939] text-white'
                            : 'hover:bg-[#fae8e8] text-arena-muted hover:text-[#d63939]'
                        }`}
                        title={isRemoved ? 'Undo remove' : 'Remove from cohort'}
                      >
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                          <path d="M3 3l6 6M9 3l-6 6" />
                        </svg>
                      </button>
                    </td>
                  )}
                  <td className="px-6 py-3">
                    <span className={`text-[13px] font-medium transition-colors ${
                      isRemoved
                        ? 'text-arena-muted line-through'
                        : 'text-arena-text group-hover:text-arena-link'
                    }`}>
                      {m.company_name}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md ${pill.bg} ${pill.text} ${isRemoved ? 'opacity-40' : ''}`}>
                      {pill.label}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-[13px] font-mono ${isRemoved ? 'text-arena-muted line-through' : 'text-arena-text-secondary'}`}>
                      {m.x_score}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-[13px] font-mono ${isRemoved ? 'text-arena-muted line-through' : 'text-arena-text-secondary'}`}>
                      {m.y_score}
                    </span>
                  </td>
                  <td className="px-4 py-3 max-w-[200px]">
                    <span className={`text-[12px] line-clamp-2 ${isRemoved ? 'text-arena-muted/50 line-through' : 'text-arena-muted'}`}>
                      {m.key_risk}
                    </span>
                  </td>
                  <td className="px-4 py-3 max-w-[250px]">
                    <span className={`text-[12px] line-clamp-2 ${isRemoved ? 'text-arena-muted/50 line-through' : 'text-arena-muted'}`}>
                      {m.ai_summary}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {sorted.length === 0 && (
        <div className="px-6 py-8 text-center text-[13px] text-arena-muted">
          No companies analyzed yet
        </div>
      )}
    </div>
  )
}
