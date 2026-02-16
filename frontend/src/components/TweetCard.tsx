import type { NewsItem } from '../types'
import { formatRelative } from '../utils/format'

function formatEngagement(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

interface Props {
  item: NewsItem
}

export default function TweetCard({ item }: Props) {
  const engagement = item.engagement || {}
  const initial = (item.author_display_name || item.author_username || 'X')[0].toUpperCase()

  return (
    <div className="px-5 py-3 border-b border-arena-border/50 hover:bg-surface-secondary/40 transition-colors">
      {/* Author row */}
      <div className="flex items-center gap-2 mb-1.5">
        {/* Avatar — initial-based (no twitter image loading since X is blocked) */}
        <div className="w-6 h-6 rounded-full bg-surface-raised flex items-center justify-center text-[10px] font-bold text-arena-text-secondary flex-shrink-0">
          {initial}
        </div>
        <div className="flex items-center gap-1.5 min-w-0 flex-1">
          <span className="text-[12px] font-semibold text-arena-text truncate">
            {item.author_display_name || 'Unknown'}
          </span>
          {item.author_username && (
            <span className="text-[11px] text-arena-muted truncate">
              @{item.author_username}
            </span>
          )}
        </div>
        <span className="text-[10px] text-arena-muted flex-shrink-0">
          {formatRelative(item.published_at)}
        </span>
      </div>

      {/* Full tweet text */}
      <p className="text-[13px] leading-relaxed text-arena-text-secondary whitespace-pre-wrap break-words">
        {item.summary || item.title}
      </p>

      {/* Engagement metrics bar */}
      {(engagement.replies || engagement.retweets || engagement.likes || engagement.impressions) ? (
        <div className="flex items-center gap-4 mt-2 text-[11px] text-arena-muted">
          {engagement.replies != null && engagement.replies > 0 && (
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              {formatEngagement(engagement.replies)}
            </span>
          )}
          {engagement.retweets != null && engagement.retweets > 0 && (
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="17 1 21 5 17 9" />
                <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                <polyline points="7 23 3 19 7 15" />
                <path d="M21 13v2a4 4 0 0 1-4 4H3" />
              </svg>
              {formatEngagement(engagement.retweets)}
            </span>
          )}
          {engagement.likes != null && engagement.likes > 0 && (
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
              </svg>
              {formatEngagement(engagement.likes)}
            </span>
          )}
          {engagement.impressions != null && engagement.impressions > 0 && (
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              {formatEngagement(engagement.impressions)}
            </span>
          )}
        </div>
      ) : null}
    </div>
  )
}
