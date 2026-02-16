import { useState, useEffect } from 'react'
import type { EvaluationResult, ReferenceCompany } from '../types'
import CompanyOverview from './CompanyOverview'
import VulnerabilityCard from './VulnerabilityCard'
import DiligenceList from './DiligenceList'

interface Props {
  evaluationId: number
  referenceCompanies: ReferenceCompany[]
  onClose: () => void
}

export default function EvaluationModal({ evaluationId, referenceCompanies, onClose }: Props) {
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`/api/evaluator/${evaluationId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setEvaluation(data)
        setLoading(false)
      })
      .catch((e) => {
        setError(e.message)
        setLoading(false)
      })
  }, [evaluationId])

  // Close on Escape key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Slide-over panel */}
      <div className="relative w-full max-w-2xl bg-surface-primary border-l border-arena-border overflow-y-auto shadow-2xl animate-slide-in-right">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-surface-primary/95 backdrop-blur-sm border-b border-arena-border px-6 py-4 flex items-center justify-between">
          <h2 className="text-[16px] font-semibold text-arena-text">
            {evaluation?.company_name || 'Loading...'}
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-tertiary text-arena-muted hover:text-arena-text transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {loading && (
            <div className="flex items-center justify-center py-16">
              <div className="flex items-center gap-3 text-[13px] text-arena-muted">
                <span className="w-2 h-2 rounded-full bg-arena-link animate-pulse" />
                Loading evaluation...
              </div>
            </div>
          )}

          {error && (
            <div className="bg-[#fae8e8] text-[#d63939] text-[13px] px-4 py-3 rounded-lg">
              Failed to load evaluation: {error}
            </div>
          )}

          {evaluation && (
            <>
              <CompanyOverview overview={evaluation.overview} />
              <VulnerabilityCard
                evaluation={evaluation}
                referenceCompanies={referenceCompanies}
              />
              <DiligenceList items={evaluation.diligence} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
