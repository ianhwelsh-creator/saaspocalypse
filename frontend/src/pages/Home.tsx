import { usePolling } from '../hooks/usePolling'
import type { BasketTimeSeriesResponse, ArenaModel, NewsItem } from '../types'
import BasketChart from '../components/BasketChart'
import BasketLegend from '../components/BasketLegend'
import ArenaChart from '../components/ArenaChart'
import NewsFeed from '../components/NewsFeed'
import FundraisingTable from '../components/FundraisingTable'
import StockTicker from '../components/StockTicker'

export default function Home() {
  const baskets = usePolling<BasketTimeSeriesResponse | null>(
    '/api/stocks/baskets', 900_000, null
  )
  const arena = usePolling<ArenaModel[]>('/api/arena/rankings', 3_600_000, [])
  const articles = usePolling<NewsItem[]>('/api/news?content_type=long_form&limit=100', 300_000, [])
  const quickhits = usePolling<NewsItem[]>('/api/news?content_type=short_form&limit=150', 300_000, [])
  const fundraising = usePolling<NewsItem[]>('/api/news/fundraising?limit=15', 300_000, [])

  return (
    <div className="h-full flex flex-col">
      {/* Scrolling stock ticker tape */}
      <StockTicker summaries={baskets.data?.summaries ?? []} />

      {/* 3-column layout */}
      <div className="flex-1 flex min-h-0">
        {/* LEFT — News Feed */}
        <div className="w-1/4 border-r border-arena-border flex flex-col min-h-0">
          <NewsFeed
            articles={articles.data}
            quickhits={quickhits.data}
            loading={articles.loading || quickhits.loading}
          />
        </div>

        {/* CENTER — Charts */}
        <div className="w-1/2 flex flex-col min-h-0 overflow-y-auto">
          {/* Baskets */}
          <div className="border-b border-arena-border">
            <BasketChart data={baskets.data} loading={baskets.loading} />
            {baskets.data?.summaries && (
              <BasketLegend
                summaries={baskets.data.summaries}
                tickerRationale={baskets.data.ticker_rationale}
                tickerChanges={baskets.data.ticker_changes}
              />
            )}
          </div>
          {/* Arena */}
          <div className="flex-1">
            <ArenaChart data={arena.data} loading={arena.loading} />
          </div>
        </div>

        {/* RIGHT — Fundraising + Metrics */}
        <div className="w-1/4 border-l border-arena-border flex flex-col min-h-0 overflow-y-auto">
          {/* Fundraising */}
          <div className="border-b border-arena-border">
            <FundraisingTable items={fundraising.data} loading={fundraising.loading} />
          </div>

          {/* Key Metrics */}
          <div className="p-5 flex-1">
            <h2 className="text-[13px] font-semibold text-arena-text mb-4">
              Key Metrics
            </h2>
            <div className="space-y-1">
              {baskets.data?.summaries?.map((s) => (
                <div key={s.zone} className="flex items-center justify-between py-2 border-b border-arena-border/50">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2.5 h-2.5 rounded" style={{ backgroundColor: s.color }} />
                    <span className="text-[13px] text-arena-text-secondary">{s.label}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[13px] font-mono text-arena-text">{s.current_value.toFixed(1)}</span>
                    <span className={`text-[12px] font-mono ${s.change_from_baseline >= 0 ? 'text-arena-positive' : 'text-arena-negative'}`}>
                      {s.change_from_baseline >= 0 ? '+' : ''}{s.change_from_baseline.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Watchlist teaser */}
            <div className="mt-8">
              <h2 className="text-[13px] font-semibold text-arena-text mb-2">
                Watchlist
              </h2>
              <p className="text-[13px] text-arena-muted leading-relaxed">
                Track companies from the{' '}
                <a href="/watchlist" className="text-arena-link hover:underline">
                  Watchlist
                </a>{' '}
                page.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
