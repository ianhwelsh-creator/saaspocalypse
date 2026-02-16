import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import type { CohortSummary } from '../types'

const STATUS_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  pending: { bg: 'bg-surface-tertiary', text: 'text-arena-muted', label: 'Pending' },
  analyzing: { bg: 'bg-[#e8f0fa]', text: 'text-[#2b7fd4]', label: 'Analyzing' },
  complete: { bg: 'bg-[#e8f5ec]', text: 'text-[#1a9d3f]', label: 'Complete' },
  error: { bg: 'bg-[#fae8e8]', text: 'text-[#d63939]', label: 'Error' },
}

export default function CohortList() {
  const navigate = useNavigate()
  const { post, loading, error } = useApi()
  const [cohorts, setCohorts] = useState<CohortSummary[]>([])
  const [name, setName] = useState('')
  const [companiesText, setCompaniesText] = useState('')

  // Parse comma-separated companies into chips
  const parsedCompanies = companiesText
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  useEffect(() => {
    fetch('/api/cohorts')
      .then((r) => r.json())
      .then(setCohorts)
      .catch(() => {})
  }, [])

  const handleCreate = async () => {
    if (!name.trim() || parsedCompanies.length === 0) return
    const result = await post<CohortSummary>('/api/cohorts', {
      name: name.trim(),
      company_names: parsedCompanies,
    })
    if (result) {
      navigate(`/cohorts/${result.id}`)
    }
  }

  const formatDate = (iso: string) => {
    const d = new Date(iso)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold text-arena-text">
          Cohort Evaluator
        </h1>
        <p className="text-[13px] text-arena-muted mt-1">
          Analyze a portfolio of companies in batch — see how they stack up on the AI disruption matrix
        </p>
      </div>

      {/* Create cohort form */}
      <div className="bg-surface-secondary rounded-xl border border-arena-border p-6">
        <h3 className="text-[15px] font-semibold text-arena-text mb-4">
          New Cohort
        </h3>

        <div className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-[12px] font-medium text-arena-muted mb-1.5 uppercase tracking-wide">
              Cohort Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., PE Portfolio Q1 2025"
              className="w-full bg-surface-primary border border-arena-border-medium rounded-lg px-4 py-3 text-[13px] text-arena-text placeholder-arena-muted focus:outline-none focus:border-arena-link focus:ring-1 focus:ring-arena-link/20 transition-colors"
            />
          </div>

          {/* Companies textarea */}
          <div>
            <label className="block text-[12px] font-medium text-arena-muted mb-1.5 uppercase tracking-wide">
              Companies (comma-separated)
            </label>
            <textarea
              value={companiesText}
              onChange={(e) => setCompaniesText(e.target.value)}
              placeholder="Salesforce, HubSpot, Monday.com, Palantir, ServiceNow..."
              rows={3}
              className="w-full bg-surface-primary border border-arena-border-medium rounded-lg px-4 py-3 text-[13px] text-arena-text placeholder-arena-muted focus:outline-none focus:border-arena-link focus:ring-1 focus:ring-arena-link/20 transition-colors resize-none"
            />
          </div>

          {/* Preview chips */}
          {parsedCompanies.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {parsedCompanies.map((c, i) => (
                <span
                  key={i}
                  className="text-[11px] font-medium px-2.5 py-1 rounded-md bg-surface-tertiary text-arena-text-secondary"
                >
                  {c}
                </span>
              ))}
              <span className="text-[11px] text-arena-muted py-1">
                — {parsedCompanies.length} compan{parsedCompanies.length === 1 ? 'y' : 'ies'}
              </span>
            </div>
          )}

          {/* Submit */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleCreate}
              disabled={loading || !name.trim() || parsedCompanies.length === 0}
              className="px-8 py-3 bg-arena-link hover:bg-[#2472c0] disabled:opacity-40 text-white text-[13px] font-medium rounded-lg transition-colors"
            >
              {loading ? 'Creating...' : 'Create Cohort'}
            </button>
            {parsedCompanies.length > 25 && (
              <span className="text-[12px] text-arena-negative">
                Maximum 25 companies per cohort
              </span>
            )}
          </div>

          {error && (
            <div className="text-arena-negative text-[12px]">{error}</div>
          )}
        </div>
      </div>

      {/* Existing cohorts list */}
      {cohorts.length > 0 && (
        <div className="bg-surface-secondary rounded-xl border border-arena-border p-6">
          <h3 className="text-[15px] font-semibold text-arena-text mb-3">
            Previous Cohorts
          </h3>
          <div className="space-y-1.5">
            {cohorts.map((c) => {
              const badge = STATUS_BADGE[c.status] || STATUS_BADGE.pending
              return (
                <button
                  key={c.id}
                  onClick={() => navigate(`/cohorts/${c.id}`)}
                  className="w-full text-left bg-surface-tertiary/50 rounded-lg p-4 hover:bg-surface-tertiary transition-colors flex items-center justify-between group"
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="text-[13px] font-medium text-arena-text-secondary group-hover:text-arena-text transition-colors">
                        {c.name}
                      </div>
                      <div className="text-[11px] text-arena-muted mt-0.5">
                        {c.total_companies} companies · {formatDate(c.created_at)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {c.status === 'analyzing' && (
                      <span className="text-[11px] text-arena-muted">
                        {c.completed_companies}/{c.total_companies}
                      </span>
                    )}
                    <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md ${badge.bg} ${badge.text}`}>
                      {badge.label}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
