import { useState, useEffect } from 'react'
import { useApi } from '../hooks/useApi'
import type { EvaluationResult, ReferenceCompany } from '../types'
import CompanyOverview from '../components/CompanyOverview'
import VulnerabilityCard from '../components/VulnerabilityCard'
import DiligenceList from '../components/DiligenceList'

const ZONE_PILL: Record<string, { bg: string; text: string }> = {
  fortress: { bg: 'bg-[#e8f5ec]', text: 'text-[#1a9d3f]' },
  adaptation: { bg: 'bg-[#e8f0fa]', text: 'text-[#2b7fd4]' },
  compression: { bg: 'bg-[#faf3e0]', text: 'text-[#d49b1a]' },
  dead: { bg: 'bg-[#fae8e8]', text: 'text-[#d63939]' },
}

export default function Evaluator() {
  const [companyName, setCompanyName] = useState('')
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null)
  const [referenceCompanies, setReferenceCompanies] = useState<ReferenceCompany[]>([])
  const [history, setHistory] = useState<EvaluationResult[]>([])
  const { post, loading, error } = useApi()

  useEffect(() => {
    fetch('/api/evaluator/reference-companies')
      .then((r) => r.json())
      .then(setReferenceCompanies)
      .catch(() => {})

    fetch('/api/evaluator/history?limit=10')
      .then((r) => r.json())
      .then(setHistory)
      .catch(() => {})
  }, [])

  const handleAnalyze = async () => {
    if (!companyName.trim()) return
    const result = await post<EvaluationResult>('/api/evaluator/analyze', {
      company_name: companyName.trim(),
    })
    if (result) {
      setEvaluation(result)
      setHistory((prev) => [result, ...prev.slice(0, 9)])
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold text-arena-text">
          AI Proof Evaluator
        </h1>
        <p className="text-[13px] text-arena-muted mt-1">
          Evaluate any SaaS company's vulnerability to AI disruption
        </p>
      </div>

      {/* Input */}
      <div className="bg-surface-secondary rounded-xl border border-arena-border p-6">
        <div className="flex gap-3">
          <input
            type="text"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            placeholder="Enter company name (e.g., Salesforce, Palantir, Monday.com)"
            className="flex-1 bg-surface-primary border border-arena-border-medium rounded-lg px-4 py-3 text-[13px] text-arena-text placeholder-arena-muted focus:outline-none focus:border-arena-link focus:ring-1 focus:ring-arena-link/20 transition-colors"
          />
          <button
            onClick={handleAnalyze}
            disabled={loading || !companyName.trim()}
            className="px-8 py-3 bg-arena-link hover:bg-[#2472c0] disabled:opacity-40 text-white text-[13px] font-medium rounded-lg transition-colors"
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
        {error && (
          <div className="text-arena-negative text-[12px] mt-2">{error}</div>
        )}
        {loading && (
          <div className="text-arena-muted text-[13px] mt-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-arena-link animate-pulse" />
            Running AI analysis... this may take 15-30 seconds
          </div>
        )}
      </div>

      {/* Results */}
      {evaluation && (
        <div className="space-y-6">
          <CompanyOverview overview={evaluation.overview} />
          <VulnerabilityCard evaluation={evaluation} referenceCompanies={referenceCompanies} />
          <DiligenceList items={evaluation.diligence} />
        </div>
      )}

      {/* History */}
      {history.length > 0 && !evaluation && (
        <div className="bg-surface-secondary rounded-xl border border-arena-border p-6">
          <h3 className="text-[15px] font-semibold text-arena-text mb-3">
            Recent Evaluations
          </h3>
          <div className="space-y-1.5">
            {history.map((e) => {
              const pill = ZONE_PILL[e.zone] || ZONE_PILL.dead
              return (
                <button
                  key={e.id}
                  onClick={() => setEvaluation(e)}
                  className="w-full text-left bg-surface-tertiary/50 rounded-lg p-3 hover:bg-surface-tertiary transition-colors flex items-center justify-between group"
                >
                  <span className="text-[13px] text-arena-text-secondary group-hover:text-arena-text transition-colors">
                    {e.company_name}
                  </span>
                  <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-md ${pill.bg} ${pill.text}`}>
                    {e.zone}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
