import type { NewsItem } from '../types'
import { formatRelative } from '../utils/format'

interface Props {
  item: NewsItem
}

export default function PodcastCard({ item }: Props) {
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block px-5 py-3 border-b border-arena-border/50 hover:bg-surface-secondary/40 transition-colors"
    >
      {/* Header row — podcast icon + show name + time */}
      <div className="flex items-center gap-2 mb-1.5">
        {/* Podcast icon */}
        <div className="w-6 h-6 rounded-md bg-[#8b5cf6]/15 flex items-center justify-center flex-shrink-0">
          <svg className="w-3.5 h-3.5 text-[#8b5cf6]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
        </div>
        <div className="flex items-center gap-1.5 min-w-0 flex-1">
          <span className="text-[12px] font-semibold text-[#8b5cf6] truncate">
            {item.feed_name || 'Podcast'}
          </span>
        </div>
        <span className="text-[10px] text-arena-muted flex-shrink-0">
          {formatRelative(item.published_at)}
        </span>
      </div>

      {/* Episode title */}
      <p className="text-[13px] leading-snug font-medium text-arena-text-secondary line-clamp-2">
        {item.title}
      </p>

      {/* Summary / key takeaways */}
      {item.summary && (
        <p className="text-[12px] leading-relaxed text-arena-muted mt-1.5 line-clamp-3">
          {item.summary}
        </p>
      )}
    </a>
  )
}
