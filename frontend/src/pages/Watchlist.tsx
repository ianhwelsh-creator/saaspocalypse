import { useState } from 'react'
import { usePolling } from '../hooks/usePolling'
import { useApi } from '../hooks/useApi'
import type { WatchlistItem } from '../types'
import WatchlistPanel from '../components/WatchlistPanel'

export default function Watchlist() {
  const [companyName, setCompanyName] = useState('')
  const [ticker, setTicker] = useState('')
  const { data: items, loading, refresh } = usePolling<WatchlistItem[]>('/api/watchlist', 60_000, [])
  const { post, del, loading: submitting, error } = useApi()

  const handleAdd = async () => {
    if (!companyName.trim()) return
    await post('/api/watchlist', {
      company_name: companyName.trim(),
      ticker: ticker.trim() || null,
    })
    setCompanyName('')
    setTicker('')
    refresh()
  }

  const handleRemove = async (id: number) => {
    await del(`/api/watchlist/${id}`)
    refresh()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Watchlist</h1>
        <p className="text-sm text-gray-400 mt-1">
          Track companies and get their latest news
        </p>
      </div>

      {/* Add form */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <div className="flex gap-3">
          <input
            type="text"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            placeholder="Company name (e.g., Salesforce)"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gray-600"
          />
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            placeholder="Ticker (optional)"
            className="w-32 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gray-600"
          />
          <button
            onClick={handleAdd}
            disabled={submitting || !companyName.trim()}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Add
          </button>
        </div>
        {error && <div className="text-red-400 text-xs mt-2">{error}</div>}
      </div>

      {/* Watchlist items */}
      {loading ? (
        <div className="text-gray-500 text-sm">Loading watchlist...</div>
      ) : items.length === 0 ? (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-12 text-center">
          <p className="text-gray-500">No companies in your watchlist yet.</p>
          <p className="text-gray-600 text-sm mt-1">Add a company above to start tracking news.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <WatchlistPanel key={item.id} item={item} onRemove={handleRemove} />
          ))}
        </div>
      )}
    </div>
  )
}
