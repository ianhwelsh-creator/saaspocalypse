import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import type { NewsletterPreview } from '../types'
import NewsletterEditor from '../components/NewsletterEditor'

const TOPICS = [
  { key: 'ai_disruption', label: 'AI Disruption' },
  { key: 'earnings', label: 'Earnings' },
  { key: 'fundraising', label: 'Fundraising' },
  { key: 'product_launch', label: 'Product Launch' },
]

const TONES = [
  { key: 'professional', label: 'Professional' },
  { key: 'casual', label: 'Casual' },
  { key: 'technical', label: 'Technical' },
]

export default function Newsletter() {
  const [timeRange, setTimeRange] = useState(7)
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [tone, setTone] = useState('professional')
  const [preview, setPreview] = useState<NewsletterPreview | null>(null)
  const { post, loading, error } = useApi()

  const toggleTopic = (key: string) => {
    setSelectedTopics((prev) =>
      prev.includes(key) ? prev.filter((t) => t !== key) : [...prev, key]
    )
  }

  const handleGenerate = async () => {
    const result = await post<NewsletterPreview>('/api/newsletter/generate', {
      time_range_days: timeRange,
      topics: selectedTopics.length > 0 ? selectedTopics : undefined,
      tone,
    })
    if (result) setPreview(result)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Newsletter Generator</h1>
        <p className="text-sm text-gray-400 mt-1">
          Generate an AI-powered SaaSpocalypse newsletter from recent news
        </p>
      </div>

      {/* Config */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-4">
        {/* Time range */}
        <div>
          <label className="text-sm font-medium text-gray-300 mb-2 block">Time Range</label>
          <div className="flex gap-2">
            {[1, 3, 7, 14, 30].map((d) => (
              <button
                key={d}
                onClick={() => setTimeRange(d)}
                className={`px-3 py-1.5 rounded text-sm transition-colors ${
                  timeRange === d
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:text-gray-200 bg-gray-800'
                }`}
              >
                {d === 1 ? '24h' : `${d}d`}
              </button>
            ))}
          </div>
        </div>

        {/* Topics */}
        <div>
          <label className="text-sm font-medium text-gray-300 mb-2 block">
            Topics (leave empty for all)
          </label>
          <div className="flex gap-2 flex-wrap">
            {TOPICS.map((t) => (
              <button
                key={t.key}
                onClick={() => toggleTopic(t.key)}
                className={`px-3 py-1.5 rounded text-sm transition-colors ${
                  selectedTopics.includes(t.key)
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-gray-200 bg-gray-800'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tone */}
        <div>
          <label className="text-sm font-medium text-gray-300 mb-2 block">Tone</label>
          <div className="flex gap-2">
            {TONES.map((t) => (
              <button
                key={t.key}
                onClick={() => setTone(t.key)}
                className={`px-3 py-1.5 rounded text-sm transition-colors ${
                  tone === t.key
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:text-gray-200 bg-gray-800'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
        >
          {loading ? 'Generating newsletter...' : 'Generate Newsletter'}
        </button>
        {error && <div className="text-red-400 text-xs">{error}</div>}
      </div>

      {/* Preview + Send */}
      {preview && (
        <NewsletterEditor subject={preview.subject} html={preview.html} />
      )}
    </div>
  )
}
