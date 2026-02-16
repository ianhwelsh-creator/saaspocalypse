import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { CohortDetail as CohortDetailType, ReferenceCompany, CohortMatrixCompany } from '../types'
import CohortProgress from '../components/CohortProgress'
import CohortTable from '../components/CohortTable'
import MatrixChart from '../components/MatrixChart'
import EvaluationModal from '../components/EvaluationModal'

export default function CohortDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [cohort, setCohort] = useState<CohortDetailType | null>(null)
  const [referenceCompanies, setReferenceCompanies] = useState<ReferenceCompany[]>([])
  const [matrixCompanies, setMatrixCompanies] = useState<CohortMatrixCompany[]>([])
  const [selectedEvalId, setSelectedEvalId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Edit mode state
  const [editMode, setEditMode] = useState(false)
  const [pendingRemovals, setPendingRemovals] = useState<Set<number>>(new Set())
  const [addCompaniesText, setAddCompaniesText] = useState('')
  const [saving, setSaving] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)

  // Fetch reference companies once
  useEffect(() => {
    fetch('/api/evaluator/reference-companies')
      .then((r) => r.json())
      .then(setReferenceCompanies)
      .catch(() => {})
  }, [])

  // Fetch cohort detail + poll while analyzing
  const startPolling = useCallback(() => {
    if (!id) return
    if (pollRef.current) clearInterval(pollRef.current)

    const fetchCohort = () => {
      fetch(`/api/cohorts/${id}`)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return r.json()
        })
        .then((data: CohortDetailType) => {
          setCohort(data)

          // Stop polling when complete or error
          if (data.status === 'complete' || data.status === 'error') {
            if (pollRef.current) {
              clearInterval(pollRef.current)
              pollRef.current = null
            }
          }
        })
        .catch((e) => {
          setError(e.message)
          if (pollRef.current) {
            clearInterval(pollRef.current)
            pollRef.current = null
          }
        })
    }

    fetchCohort()
    pollRef.current = setInterval(fetchCohort, 3000)
  }, [id])

  useEffect(() => {
    startPolling()
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [startPolling])

  // Fetch matrix companies when cohort is complete
  useEffect(() => {
    if (!id || !cohort || cohort.status !== 'complete') return

    fetch(`/api/cohorts/${id}/matrix`)
      .then((r) => r.json())
      .then(setMatrixCompanies)
      .catch(() => {})
  }, [id, cohort?.status])

  // Edit mode handlers
  const handleToggleRemove = (evalId: number) => {
    setPendingRemovals((prev) => {
      const next = new Set(prev)
      if (next.has(evalId)) {
        next.delete(evalId)
      } else {
        next.add(evalId)
      }
      return next
    })
  }

  const parsedAddCompanies = addCompaniesText
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  const handleSaveEdit = async () => {
    if (!id) return
    if (pendingRemovals.size === 0 && parsedAddCompanies.length === 0) return

    setSaving(true)
    setEditError(null)

    try {
      const res = await fetch(`/api/cohorts/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          add_companies: parsedAddCompanies,
          remove_evaluation_ids: Array.from(pendingRemovals),
        }),
      })

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail || `HTTP ${res.status}`)
      }

      const updated: CohortDetailType = await res.json()
      setCohort(updated)

      // Reset edit mode
      setEditMode(false)
      setPendingRemovals(new Set())
      setAddCompaniesText('')

      // If new companies were added, restart polling for analysis progress
      if (parsedAddCompanies.length > 0 && updated.status === 'analyzing') {
        startPolling()
      }

      // Re-fetch matrix if still complete (removals only)
      if (updated.status === 'complete') {
        fetch(`/api/cohorts/${id}/matrix`)
          .then((r) => r.json())
          .then(setMatrixCompanies)
          .catch(() => {})
      }
    } catch (e) {
      setEditError(e instanceof Error ? e.message : 'Failed to save changes')
    } finally {
      setSaving(false)
    }
  }

  const handleCancelEdit = () => {
    setEditMode(false)
    setPendingRemovals(new Set())
    setAddCompaniesText('')
    setEditError(null)
  }

  if (error) {
    return (
      <div className="p-8 max-w-5xl mx-auto">
        <div className="bg-[#fae8e8] text-[#d63939] text-[13px] px-4 py-3 rounded-lg">
          Failed to load cohort: {error}
        </div>
      </div>
    )
  }

  if (!cohort) {
    return (
      <div className="p-8 max-w-5xl mx-auto">
        <div className="flex items-center gap-3 text-[13px] text-arena-muted py-16 justify-center">
          <span className="w-2 h-2 rounded-full bg-arena-link animate-pulse" />
          Loading cohort...
        </div>
      </div>
    )
  }

  const hasChanges = pendingRemovals.size > 0 || parsedAddCompanies.length > 0

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate('/cohorts')}
            className="text-[12px] text-arena-muted hover:text-arena-text transition-colors mb-2 flex items-center gap-1"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M7 3L4 6l3 3" />
            </svg>
            Back to Cohorts
          </button>
          <h1 className="text-[22px] font-semibold text-arena-text">
            {cohort.name}
          </h1>
          <p className="text-[13px] text-arena-muted mt-1">
            {cohort.total_companies} companies · Created {new Date(cohort.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
          </p>
        </div>

        {/* Edit button — only when complete and not already editing */}
        {cohort.status === 'complete' && !editMode && (
          <button
            onClick={() => setEditMode(true)}
            className="px-4 py-2 text-[12px] font-medium text-arena-text-secondary border border-arena-border-medium rounded-lg hover:bg-surface-tertiary transition-colors"
          >
            Edit Cohort
          </button>
        )}
      </div>

      {/* Progress (shown during analysis or when pending) */}
      {(cohort.status === 'analyzing' || cohort.status === 'pending') && (
        <CohortProgress cohort={cohort} />
      )}

      {/* Table — show as soon as we have members */}
      {cohort.members.length > 0 && (
        <CohortTable
          members={cohort.members}
          onSelectMember={(evalId) => setSelectedEvalId(evalId)}
          editMode={editMode}
          onRemoveMember={handleToggleRemove}
          pendingRemovals={pendingRemovals}
        />
      )}

      {/* Edit mode — add companies form + save/cancel */}
      {editMode && (
        <div className="bg-surface-secondary rounded-xl border border-arena-border p-6 space-y-4">
          <h3 className="text-[15px] font-semibold text-arena-text">
            Add Companies
          </h3>

          <div>
            <textarea
              value={addCompaniesText}
              onChange={(e) => setAddCompaniesText(e.target.value)}
              placeholder="Enter company names separated by commas (e.g., Constant Contact, SurveyMonkey)"
              rows={2}
              className="w-full bg-surface-primary border border-arena-border-medium rounded-lg px-4 py-3 text-[13px] text-arena-text placeholder-arena-muted focus:outline-none focus:border-arena-link focus:ring-1 focus:ring-arena-link/20 transition-colors resize-none"
            />
          </div>

          {/* Preview chips for new companies */}
          {parsedAddCompanies.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {parsedAddCompanies.map((c, i) => (
                <span
                  key={i}
                  className="text-[11px] font-medium px-2.5 py-1 rounded-md bg-[#e8f5ec] text-[#1a9d3f]"
                >
                  + {c}
                </span>
              ))}
            </div>
          )}

          {/* Summary of changes */}
          {hasChanges && (
            <div className="text-[12px] text-arena-muted">
              {pendingRemovals.size > 0 && (
                <span className="text-[#d63939]">
                  {pendingRemovals.size} compan{pendingRemovals.size === 1 ? 'y' : 'ies'} to remove
                </span>
              )}
              {pendingRemovals.size > 0 && parsedAddCompanies.length > 0 && ' · '}
              {parsedAddCompanies.length > 0 && (
                <span className="text-[#1a9d3f]">
                  {parsedAddCompanies.length} compan{parsedAddCompanies.length === 1 ? 'y' : 'ies'} to add
                </span>
              )}
            </div>
          )}

          {editError && (
            <div className="text-[12px] text-arena-negative">{editError}</div>
          )}

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleSaveEdit}
              disabled={saving || !hasChanges}
              className="px-6 py-2.5 bg-arena-link hover:bg-[#2472c0] disabled:opacity-40 text-white text-[13px] font-medium rounded-lg transition-colors"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            <button
              onClick={handleCancelEdit}
              disabled={saving}
              className="px-6 py-2.5 text-[13px] font-medium text-arena-text-secondary hover:text-arena-text transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Matrix — show when complete and we have matrix data */}
      {cohort.status === 'complete' && matrixCompanies.length > 0 && (
        <div className="bg-surface-secondary rounded-xl border border-arena-border p-6">
          <h3 className="text-[15px] font-semibold text-arena-text mb-4">
            AI Disruption Matrix
          </h3>
          <MatrixChart
            referenceCompanies={referenceCompanies}
            cohortCompanies={matrixCompanies}
            hideReference
          />
        </div>
      )}

      {/* Evaluation detail modal */}
      {selectedEvalId !== null && (
        <EvaluationModal
          evaluationId={selectedEvalId}
          referenceCompanies={referenceCompanies}
          onClose={() => setSelectedEvalId(null)}
        />
      )}
    </div>
  )
}
