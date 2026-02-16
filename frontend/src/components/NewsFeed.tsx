import { useState, useMemo } from 'react'
import type { NewsItem } from '../types'
import { formatRelative } from '../utils/format'
import SourceBadge from './SourceBadge'
import TweetCard from './TweetCard'

// ── Per-tab source filters ───────────────────────────────────────────────────
const ARTICLE_SOURCES = [
  { key: '', label: 'All' },
  { key: 'institutional', label: 'Inst.' },
  { key: 'techcrunch', label: 'TC' },
  { key: 'rss', label: 'RSS' },
  { key: 'newsapi', label: 'MS' },
]

const QUICKHIT_SOURCES = [
  { key: '', label: 'All' },
  { key: 'twitter', label: 'X' },
  { key: 'reddit', label: 'Reddit' },
  { key: 'hackernews', label: 'HN' },
]

// Institutional source keys that should match the "Inst." filter
const INSTITUTIONAL_SOURCES = new Set(['wsj', 'reuters', 'ft', 'bloomberg', 'cnbc', 'institutional'])

const ZONE_COLORS: Record<string, { color: string; bg: string }> = {
  'Fortress Zone': { color: '#1a9d3f', bg: '#1a9d3f14' },
  'Dead Zone': { color: '#dc2626', bg: '#dc262614' },
  'Compression Zone': { color: '#d49b1a', bg: '#d49b1a14' },
  'Adaptation Zone': { color: '#2b7fd4', bg: '#2b7fd414' },
  'Macro': { color: '#8b5cf6', bg: '#8b5cf614' },
  'Earnings': { color: '#6b7280', bg: '#6b728014' },
}

function scoreColor(score: number): string {
  if (score >= 50) return '#1a9d3f'
  if (score >= 35) return '#2b7fd4'
  if (score >= 20) return '#d49b1a'
  return '#8a8480'
}

function scoreBg(score: number): string {
  if (score >= 50) return '#1a9d3f14'
  if (score >= 35) return '#2b7fd414'
  if (score >= 20) return '#d49b1a14'
  return '#8a848010'
}

interface Props {
  items: NewsItem[]
  loading: boolean
}

export default function NewsFeed({ items, loading }: Props) {
  const [tab, setTab] = useState<'articles' | 'quickhits'>('articles')
  const [articleSource, setArticleSource] = useState('')
  const [quickhitSource, setQuickhitSource] = useState('')
  const [sortBy, setSortBy] = useState<'score' | 'recent'>('score')

  // Split items by content_type
  const { articles, quickhits } = useMemo(() => {
    const arts: NewsItem[] = []
    const qh: NewsItem[] = []
    for (const item of items) {
      if (item.content_type === 'short_form') {
        qh.push(item)
      } else {
        // long_form or unclassified → articles
        arts.push(item)
      }
    }
    return { articles: arts, quickhits: qh }
  }, [items])

  // Current active source filter
  const source = tab === 'articles' ? articleSource : quickhitSource
  const setSource = tab === 'articles' ? setArticleSource : setQuickhitSource
  const sourceList = tab === 'articles' ? ARTICLE_SOURCES : QUICKHIT_SOURCES
  const baseItems = tab === 'articles' ? articles : quickhits

  // Apply source filter
  let filtered = baseItems.filter((item) => {
    if (!source) return true
    if (source === 'institutional') return INSTITUTIONAL_SOURCES.has(item.source)
    return item.source === source
  })

  // Client-side re-sort when toggling
  if (sortBy === 'recent') {
    filtered = [...filtered].sort(
      (a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
    )
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Header */}
      <div className="px-5 py-3 border-b border-arena-border flex-shrink-0">
        <div className="flex items-center justify-between">
          <h2 className="text-[13px] font-semibold text-arena-text">
            Latest News
          </h2>
          {/* Sort toggle */}
          <div className="flex bg-surface-tertiary rounded-md p-0.5">
            <button
              onClick={() => setSortBy('score')}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                sortBy === 'score'
                  ? 'bg-surface-secondary text-arena-text shadow-sm'
                  : 'text-arena-muted hover:text-arena-text-tertiary'
              }`}
            >
              Top
            </button>
            <button
              onClick={() => setSortBy('recent')}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                sortBy === 'recent'
                  ? 'bg-surface-secondary text-arena-text shadow-sm'
                  : 'text-arena-muted hover:text-arena-text-tertiary'
              }`}
            >
              New
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-2.5 border-b border-arena-border/50 -mx-5 px-5">
          <button
            onClick={() => setTab('articles')}
            className={`pb-2 px-1 text-[12px] font-semibold transition-colors border-b-2 ${
              tab === 'articles'
                ? 'text-arena-text border-arena-accent'
                : 'text-arena-muted border-transparent hover:text-arena-text-tertiary'
            }`}
          >
            Articles{articles.length > 0 ? ` (${articles.length})` : ''}
          </button>
          <button
            onClick={() => setTab('quickhits')}
            className={`pb-2 px-1 text-[12px] font-semibold transition-colors border-b-2 ${
              tab === 'quickhits'
                ? 'text-arena-text border-arena-accent'
                : 'text-arena-muted border-transparent hover:text-arena-text-tertiary'
            }`}
          >
            Quick Hits{quickhits.length > 0 ? ` (${quickhits.length})` : ''}
          </button>
        </div>

        {/* Source filter */}
        <div className="flex gap-1 mt-2 flex-wrap">
          {sourceList.map((s) => (
            <button
              key={s.key}
              onClick={() => setSource(s.key)}
              className={`px-2 py-1 rounded-md text-[11px] font-medium transition-colors ${
                source === s.key
                  ? 'bg-surface-raised text-arena-text'
                  : 'text-arena-muted hover:text-arena-text-tertiary'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Feed */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center text-arena-muted text-[13px]">
          Loading...
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="px-5 py-8 text-center text-arena-muted text-[12px]">
              No items yet
            </div>
          ) : (
            filtered.map((item, i) =>
              tab === 'quickhits' && item.source === 'twitter' ? (
                <TweetCard key={`${item.url}-${i}`} item={item} />
              ) : (
                <a
                  key={`${item.url}-${i}`}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block px-5 py-3 border-b border-arena-border/50 hover:bg-surface-secondary/40 transition-colors"
                >
                  <p className="text-[13px] leading-snug font-medium text-arena-text-secondary line-clamp-2">
                    {item.title}
                  </p>
                  {/* AI summary for institutional items */}
                  {item.ai_summary && (
                    <p className="text-[11px] text-arena-muted mt-1 line-clamp-1 italic">
                      {item.ai_summary}
                    </p>
                  )}
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <SourceBadge source={item.source} />
                    {/* Zone tag */}
                    {item.zone_tag && (
                      <span
                        className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full uppercase tracking-wide"
                        style={{
                          color: ZONE_COLORS[item.zone_tag]?.color || '#6b7280',
                          backgroundColor: ZONE_COLORS[item.zone_tag]?.bg || '#6b728014',
                        }}
                      >
                        {item.zone_tag}
                      </span>
                    )}
                    {/* Score pill */}
                    {item.score != null && item.score > 0 && (
                      <span
                        className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-md"
                        style={{
                          color: scoreColor(item.score),
                          backgroundColor: scoreBg(item.score),
                        }}
                      >
                        {item.score}
                      </span>
                    )}
                    <span className="text-[11px] text-arena-muted">
                      {formatRelative(item.published_at)}
                    </span>
                    {/* Feed name for RSS and institutional sources */}
                    {item.feed_name && (item.source === 'rss' || INSTITUTIONAL_SOURCES.has(item.source)) && (
                      <span className="text-[10px] text-arena-muted truncate max-w-[100px]">
                        {item.feed_name}
                      </span>
                    )}
                    {/* Reddit/HN engagement */}
                    {item.source === 'reddit' && item.engagement?.score != null && item.engagement.score > 0 && (
                      <span className="text-[10px] text-arena-muted">
                        {item.engagement.score} pts
                      </span>
                    )}
                    {item.source === 'hackernews' && item.engagement?.points != null && item.engagement.points > 0 && (
                      <span className="text-[10px] text-arena-muted">
                        {item.engagement.points} pts
                      </span>
                    )}
                  </div>
                </a>
              )
            )
          )}
        </div>
      )}
    </div>
  )
}
