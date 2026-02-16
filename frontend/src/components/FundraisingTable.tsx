import type { NewsItem } from '../types'
import { formatRelative } from '../utils/format'
import SourceBadge from './SourceBadge'

interface Props {
  items: NewsItem[]
  loading: boolean
}

export default function FundraisingTable({ items, loading }: Props) {
  if (loading) {
    return (
      <div className="p-5">
        <div className="h-32 flex items-center justify-center text-arena-muted text-[13px]">
          Loading fundraising...
        </div>
      </div>
    )
  }

  return (
    <div className="p-5">
      <h2 className="text-[13px] font-semibold text-arena-text mb-3">
        Recent Fundraising
      </h2>

      {items.length === 0 ? (
        <div className="text-arena-muted text-[13px] py-4 text-center">No fundraising data</div>
      ) : (
        <div>
          {items.map((item, i) => (
            <a
              key={`${item.url}-${i}`}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block py-2.5 border-b border-arena-border/50 hover:bg-surface-secondary/30 transition-colors"
            >
              <p className="text-[12px] leading-snug text-arena-text-secondary line-clamp-2">
                {item.title}
              </p>
              <div className="flex items-center gap-2 mt-1.5">
                <SourceBadge source={item.source} />
                <span className="text-[11px] text-arena-muted">
                  {formatRelative(item.published_at)}
                </span>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}
