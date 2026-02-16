import { useState, useEffect } from 'react'
import type { WatchlistItem, NewsItem } from '../types'
import NewsCard from './NewsCard'

interface Props {
  item: WatchlistItem
  onRemove: (id: number) => void
}

export default function WatchlistPanel({ item, onRemove }: Props) {
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    if (!expanded) return
    setLoading(true)
    fetch(`/api/watchlist/${item.id}/news`)
      .then((r) => r.json())
      .then((data) => setNews(data))
      .catch(() => setNews([]))
      .finally(() => setLoading(false))
  }, [item.id, expanded])

  return (
    <div className="bg-gray-800/40 rounded-lg border border-gray-700/50 p-4">
      <div className="flex items-center justify-between">
        <div
          className="flex items-center gap-3 cursor-pointer flex-1"
          onClick={() => setExpanded(!expanded)}
        >
          <div>
            <span className="text-sm font-medium text-gray-200">{item.company_name}</span>
            {item.ticker && (
              <span className="text-xs text-gray-500 ml-2">{item.ticker}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-gray-400 hover:text-gray-200 px-2 py-1"
          >
            {expanded ? 'Collapse' : 'News'}
          </button>
          <button
            onClick={() => onRemove(item.id)}
            className="text-xs text-red-400 hover:text-red-300 px-2 py-1"
          >
            Remove
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-gray-700/50">
          {loading ? (
            <div className="text-gray-500 text-xs py-4 text-center">Loading news...</div>
          ) : news.length === 0 ? (
            <div className="text-gray-500 text-xs py-4 text-center">No recent news found</div>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {news.slice(0, 10).map((n, i) => (
                <NewsCard key={`${n.url}-${i}`} item={n} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
