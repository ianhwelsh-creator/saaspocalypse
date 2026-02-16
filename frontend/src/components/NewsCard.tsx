import type { NewsItem } from '../types'
import { formatRelative } from '../utils/format'
import SourceBadge from './SourceBadge'

export default function NewsCard({ item }: { item: NewsItem }) {
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-gray-800/40 rounded-lg border border-gray-700/50 p-4 hover:border-gray-600 transition-colors"
    >
      <div className="flex items-start gap-3">
        {item.image_url && (
          <img
            src={item.image_url}
            alt=""
            className="w-16 h-16 rounded object-cover flex-shrink-0"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        )}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-gray-200 line-clamp-2">
            {item.title}
          </h3>
          {item.summary && (
            <p className="text-xs text-gray-400 mt-1 line-clamp-2">
              {item.summary}
            </p>
          )}
          <div className="flex items-center gap-2 mt-2">
            <SourceBadge source={item.source} />
            {item.category && (
              <span className="text-xs text-gray-500">{item.category.replace('_', ' ')}</span>
            )}
            <span className="text-xs text-gray-500">{formatRelative(item.published_at)}</span>
          </div>
        </div>
      </div>
    </a>
  )
}
