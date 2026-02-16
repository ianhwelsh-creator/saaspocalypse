// --- Stocks ---

export interface BasketDataPoint {
  date: string
  dead_zone?: number
  compression_zone?: number
  adaptation_zone?: number
  fortress_zone?: number
  ai_etfs?: number
}

export interface BasketSummary {
  zone: string
  label: string
  current_value: number
  change_from_baseline: number
  color: string
  tickers: string[]
}

export interface BasketTimeSeriesResponse {
  series: BasketDataPoint[]
  summaries: BasketSummary[]
  baseline_date: string
}

export interface StockDetail {
  ticker: string
  name: string
  current_price: number
  change_pct: number
}

// --- Arena ---

export interface ArenaModel {
  rank: number
  model_name: string
  elo_score: number
  organization: string
  ai_spend_billions: number | null
}

// --- News ---

export interface NewsEngagement {
  points?: number
  comments?: number
  score?: number
  likes?: number
  retweets?: number
  replies?: number
  impressions?: number
}

export interface NewsItem {
  id?: number
  title: string
  url: string
  source: string
  category?: string
  summary?: string
  image_url?: string
  published_at: string
  feed_name?: string
  subreddit?: string
  score?: number
  engagement?: NewsEngagement
  zone_tag?: string
  ai_relevance_score?: number
  ai_summary?: string
  content_type?: 'long_form' | 'short_form'
  author_username?: string
  author_display_name?: string
  author_profile_image?: string
}

// --- Watchlist ---

export interface WatchlistItem {
  id: number
  company_name: string
  ticker: string | null
  added_at: string
}

// --- Evaluator ---

export interface ReferenceCompany {
  name: string
  ticker: string
  zone: string
  x: number
  y: number
  bullets: string[]
  logo_url?: string
}

export interface EvaluationResult {
  id?: number
  company_name: string
  zone: string
  overview: string
  justification: string
  diligence: string[]
  x_score: number
  y_score: number
  created_at?: string
}

// --- Cohorts ---

export interface CohortSummary {
  id: number
  name: string
  status: 'pending' | 'analyzing' | 'complete' | 'error'
  total_companies: number
  completed_companies: number
  current_company: string | null
  created_at: string
}

export interface CohortMemberSummary {
  evaluation_id: number
  company_name: string
  zone: string
  x_score: number
  y_score: number
  key_risk: string
  ai_summary: string
}

export interface CohortDetail extends CohortSummary {
  members: CohortMemberSummary[]
}

export interface CohortMatrixCompany extends ReferenceCompany {
  is_cohort?: boolean
}

export interface CohortEditRequest {
  add_companies: string[]
  remove_evaluation_ids: number[]
}

// --- Newsletter ---

export interface NewsletterPreview {
  subject: string
  html: string
}
