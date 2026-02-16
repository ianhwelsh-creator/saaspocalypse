# SaaSpocalypse - Feature Breakdown

> A real-time intelligence platform tracking AI disruption across the SaaS landscape. Built on the **"Don't Short SaaS"** 2x2 framework: Workflow Complexity vs. Data Moat Depth.

**Stack**: React 19 + TypeScript + Vite + Tailwind | FastAPI + SQLAlchemy (async) + SQLite | Claude AI + yfinance + RSS/News APIs

---

## Table of Contents

1. [Dashboard (Home)](#1-dashboard-home)
2. [News Aggregation Pipeline](#2-news-aggregation-pipeline)
3. [Stock Basket Tracker](#3-stock-basket-tracker)
4. [LLM Arena Leaderboard](#4-llm-arena-leaderboard)
5. [AI Proof Evaluator](#5-ai-proof-evaluator)
6. [Company Watchlist](#6-company-watchlist)
7. [Newsletter Generator](#7-newsletter-generator)
8. [Background Scheduler](#8-background-scheduler)
9. [API Reference](#9-api-reference)
10. [Data Models & Scoring](#10-data-models--scoring)
11. [Architecture](#11-architecture)

---

## 1. Dashboard (Home)

**Page**: `frontend/src/pages/Home.tsx`

Three-column real-time dashboard:

| Column | Width | Content | Poll Interval |
|--------|-------|---------|---------------|
| Left | 1/4 | News Feed | 5 min |
| Center | 1/2 | Stock Baskets + Arena Rankings | 15 min / 1 hr |
| Right | 1/4 | Fundraising Table + Key Metrics | 5 min |

- All data auto-refreshes via `usePolling` hook (configurable intervals)
- Arena light-mode design system with custom Tailwind tokens (`surface-*`, `arena-*`)
- Live indicator in top nav shows real-time connection status

---

## 2. News Aggregation Pipeline

### 2.1 Sources (6 total)

| Source | Client | Key Required | Items |
|--------|--------|-------------|-------|
| Google News RSS (Institutional) | `institutional_client.py` | None | WSJ, Reuters, FT, Bloomberg, CNBC |
| RSS/Atom Feeds | `rss_client.py` | None | 12 feeds (HN, TechCrunch, Reddit x4, Substacks, Ars Technica, The Verge, Techmeme) |
| Mediastack | `news_client.py` | `MEDIASTACK_KEY` | General news API (free tier, 500 req/mo) |
| Twitter/X v2 | `twitter_client.py` | `TWITTER_BEARER_TOKEN` | Recent tweets with engagement metrics |
| Claude AI Filter | `claude_client.py` | `ANTHROPIC_API_KEY` | Scores institutional items for relevance |

### 2.2 Aggregation Flow

```
Institutional (Google News RSS)
    -> Claude AI filter (relevance 50+ threshold)
        -> zone_tag (dead/compression/adaptation/fortress)
        -> ai_summary (one-line context)
        -> ai_relevance_score (0-100)
    -> RSS feeds (12 concurrent)
    -> Mediastack API
    -> Twitter/X API
        -> Merge all sources
        -> Deduplicate (rapidfuzz, 80%+ title similarity)
        -> Categorize (AI_disruption, fundraising, earnings, product_launch)
        -> Composite score (0-100)
        -> Sort & serve
```

### 2.3 Composite Scoring Formula

| Factor | Weight | How It Works |
|--------|--------|-------------|
| **Relevance** | 0-40 pts | Keyword tiers: "disruption" (8), "SaaS" (5), "AI" (4), "impact" (3), general (1) |
| **Popularity** | 0-30 pts | Log-scaled engagement: HN points+comments/10, Reddit log2(score)*3, Twitter log2(likes+retweets*3)*3 |
| **Authority** | 0-20 pts | Source weight: WSJ/Stratechery = 20, HN = 12, r/SaaS = 10, Unknown = 8 |
| **Recency** | 0-10 pts | Exponential decay: 2h = 10, 6h = 8, 12h = 6, 24h = 4, 48h = 2 |

**Claude AI Bonus** (institutional items only):
- CRITICAL (score 90+): +15 points
- HIGH (75-89): +10 points
- MODERATE (50-74): +5 points

### 2.4 Frontend Components

- **`NewsFeed.tsx`**: Left panel with source filter chips (All, Inst., HN, TC, Reddit, X, RSS, MS), sort toggle (Top/New), zone color tags, AI summaries, score pills
- **`FundraisingTable.tsx`**: Right panel compact list of fundraising-category news
- **`SourceBadge.tsx`**: Color-coded badges (HN orange, TC green, Reddit red, WSJ/BBG dark, Reuters orange, FT tan, CNBC blue)
- **`NewsCard.tsx`**: Full card with thumbnail, title, summary, metadata (used in watchlist)

**Backend**: `services/news_aggregator.py` (merge + score + dedup), `routers/news.py` (2 endpoints)

---

## 3. Stock Basket Tracker

### 3.1 Zone Baskets (5 baskets, 26 tickers)

| Zone | Color | Tickers | Thesis |
|------|-------|---------|--------|
| **Dead Zone** | Red | FRSH, ZS, ASAN, MDB, FIVN | Existential AI threat - simple workflows, weak moats |
| **Compression Zone** | Amber | HUBS, BILL, ZI, SEMR, BRZE | Margin pressure - AI commoditizes their features |
| **Adaptation Zone** | Blue | ADBE, TEAM, DOCN, TWLO, DDOG | Must embed AI fast or lose relevance |
| **Fortress Zone** | Emerald | VEEV, NOW, CRWD, SNOW, PCOR, GWRE | AI strengthens competitive position |
| **AI ETFs** | Purple | BOTZ, AIQ, ROBT | Benchmark comparison |

### 3.2 Indexing Method

- **Baseline date**: January 30, 2026 (indexed to 100)
- **Calculation**: Equal-weight average of (close_price / baseline_price * 100) per basket
- **Data source**: yfinance with 15-minute in-memory cache
- Handles missing data gracefully (uses available tickers only)

### 3.3 Frontend

- **`BasketChart.tsx`**: Recharts `LineChart` with 5 colored lines, reference line at 100
  - Range filters: ALL, 3M, 1M, 1W
  - Dynamic Y-axis scaling with 10% padding
  - Custom tooltip with all basket values
- **`BasketLegend.tsx`**: 2-column grid of zone summary cards showing change %, tagline, axis info, constituent tickers

**Backend**: `services/stock_service.py` (indexing logic), `apis/stock_client.py` (yfinance wrapper), `seed/baskets.py` (ticker definitions)

---

## 4. LLM Arena Leaderboard

### 4.1 Data Source

- **Primary**: Live scrape of `arena.ai/leaderboard` (BeautifulSoup, text arena table)
- **Fallback**: Static rankings (12 models, hardcoded with Elo scores)
- **Backfill**: If live scrape is missing orgs (e.g. Meta, DeepSeek), appends them from static data
- **Cache**: 1-hour TTL in-memory

### 4.2 Model Name Cleaning Pipeline

```
Raw scraped name
    -> Strip org prefix ("Anthropicclaude-opus-4-6-thinking" -> "claude-opus-4-6-thinking")
    -> Replace hyphens with spaces
    -> Brand capitalization (Claude, Gemini, Grok, GPT, Llama, DeepSeek)
    -> Version merging ("4 6" -> "4.6")
    -> Mode parenthesizing ("thinking" -> "(Thinking)")
    -> Date stamp removal (8-digit numbers)
```

### 4.3 AI Capex / Fundraising Data (2026)

| Company | Spend ($B) | Type |
|---------|-----------|------|
| Amazon/AWS | $200B | Guided capex |
| Alphabet/Google | $180B | Guided capex |
| Microsoft | $145B | Annualized capex |
| Meta | $125B | Guided capex |
| OpenAI | $60B | Total raised |
| Anthropic | $37B | Total raised |
| Apple | $30B | Estimated capex |
| xAI | $22B | Total raised |
| Oracle | $16B | Estimated capex |

### 4.4 Frontend

- **`ArenaChart.tsx`**: Custom horizontal bar chart (no charting library)
  - Proportional Elo score bars with org brand colors
  - Google Favicons API for company logos (`google.com/s2/favicons?domain={domain}&sz=128`)
  - 7 distinct org colors (OpenAI teal, Anthropic coral, Google blue, Meta blue, xAI gray, DeepSeek blue, Mistral orange)
  - AI spend legend below chart: "2026 AI Capex / Total Raised"

**Backend**: `services/arena_service.py` (enrichment), `apis/arena_client.py` (scraper), `seed/ai_spend.py` (spend data)

---

## 5. AI Proof Evaluator

### 5.1 Overview

AI-powered company vulnerability assessment using Claude Sonnet 4.5. Positions any company on the "Don't Short SaaS" 2x2 matrix.

### 5.2 Analysis Output

| Field | Type | Description |
|-------|------|-------------|
| `company_name` | string | Normalized company name |
| `zone` | enum | dead / compression / adaptation / fortress |
| `x_score` | 0-100 | Workflow Complexity (low = simple/templated, high = judgment-intensive) |
| `y_score` | 0-100 | Data Moat Depth (low = replicable, high = proprietary/mandated) |
| `overview` | string | Multi-paragraph company analysis |
| `justification` | string | Why this zone placement |
| `diligence` | string[] | 5-8 AI-proof diligence checkpoints |

### 5.3 2x2 Matrix Visualization

```
         High Moat
            |
  Compression  |  Fortress
  (Amber)      |  (Green)
 ------------- + -------------
  Dead Zone    |  Adaptation
  (Red)        |  (Blue)
            |
         Low Moat
  Low Complexity    High Complexity
```

### 5.4 Reference Companies (12 pre-positioned)

Permanently plotted on the matrix for context:
- **Fortress**: Veeva (VEEV), ServiceNow (NOW), CrowdStrike (CRWD)
- **Adaptation**: Adobe (ADBE), Atlassian (TEAM), Datadog (DDOG)
- **Compression**: HubSpot (HUBS), Bill.com (BILL), ZoomInfo (ZI)
- **Dead Zone**: Freshworks (FRSH), Asana (ASAN), Five9 (FIVN)

Each has a logo, ticker, 3 bullet points, and fixed x/y coordinates.

### 5.5 Frontend

- **`Evaluator.tsx`**: Page with company input, analysis display, history sidebar
- **`MatrixChart.tsx`**: Interactive SVG 2x2 chart with:
  - Quadrant color backgrounds
  - 12 reference company circles (hover for tooltip with name, ticker, bullets)
  - Evaluated company marked with gold star + glow animation
  - Logo images with fallback to ticker abbreviation
- **`CompanyOverview.tsx`**: Multi-paragraph overview renderer
- **`VulnerabilityCard.tsx`**: Zone badge, x/y score progress bars, justification text
- **`DiligenceList.tsx`**: Numbered checklist of AI-proof items

**Backend**: `services/evaluator_service.py` (orchestration + DB caching), `apis/claude_client.py` (AI analysis), `seed/zone_companies.py` (reference data)

---

## 6. Company Watchlist

### 6.1 Functionality

- **Add**: Company name + optional ticker symbol
- **List**: All watched companies with expand/collapse cards
- **Remove**: Delete from watchlist
- **News Search**: Per-company news aggregation (HN search + all feeds, filtered by company name)

### 6.2 Frontend

- **`Watchlist.tsx`**: Page with add form + company cards grid
- **`WatchlistPanel.tsx`**: Expandable card per company with inline news feed (uses `NewsCard` children)

**Backend**: `routers/watchlist.py` (CRUD + news search), DB table `WatchlistItem`

---

## 7. Newsletter Generator

### 7.1 Configuration

| Parameter | Options | Default |
|-----------|---------|---------|
| Time Range | 1, 3, 7, 14, 30 days | 7 |
| Topics | AI Disruption, Earnings, Fundraising, Product Launch | All |
| Tone | Professional, Casual, Technical | Professional |

### 7.2 Generation Flow

```
1. Fetch top 50 news items (from aggregator cache)
2. Filter by selected topics (if any)
3. Send to Claude with newsletter system prompt
4. Claude returns: { subject: string, html: string }
5. Frontend renders HTML preview
6. User inputs email + clicks Send
7. Resend API delivers newsletter from newsletter@saaspocalypse.com
```

### 7.3 Frontend

- **`Newsletter.tsx`**: Page with config form (time range, topic checkboxes, tone selector), generate button
- **`NewsletterEditor.tsx`**: HTML preview pane, email input, send button with confirmation

**Backend**: `services/newsletter_service.py` (Claude generation + Resend delivery), `apis/claude_client.py` (generate_newsletter), `apis/email_client.py` (Resend wrapper)

---

## 8. Background Scheduler

**Service**: `services/scheduler.py` (APScheduler)

| Job | Interval | What It Does |
|-----|----------|-------------|
| `refresh_news` | 15 min | Full aggregation pipeline (institutional + Claude filter + RSS + Mediastack + Twitter) |
| `refresh_fundraising` | 15 min | Fundraising-category aggregation |

Configured via `NEWS_REFRESH_INTERVAL_MINUTES` in `config.py`.

---

## 9. API Reference

### Stocks

| Method | Endpoint | Params | Response |
|--------|----------|--------|----------|
| `GET` | `/api/stocks/baskets` | `?end_date=YYYY-MM-DD` | `BasketTimeSeriesResponse` (time series + summaries) |
| `GET` | `/api/stocks/baskets/{zone}` | zone name | `StockDetail[]` (individual stock prices) |

### Arena

| Method | Endpoint | Params | Response |
|--------|----------|--------|----------|
| `GET` | `/api/arena/rankings` | `?top_n=15` | `ArenaModel[]` (rank, name, elo, org, spend) |

### News

| Method | Endpoint | Params | Response |
|--------|----------|--------|----------|
| `GET` | `/api/news` | `?category=X&source=Y&sort=score&limit=50&offset=0` | `NewsItem[]` |
| `GET` | `/api/news/fundraising` | `?limit=20` | `NewsItem[]` |

### Watchlist

| Method | Endpoint | Body/Params | Response |
|--------|----------|-------------|----------|
| `GET` | `/api/watchlist` | - | `WatchlistItem[]` |
| `POST` | `/api/watchlist` | `{company_name, ticker?}` | `WatchlistItem` |
| `DELETE` | `/api/watchlist/{id}` | id | `{ok: true}` |
| `GET` | `/api/watchlist/{id}/news` | id | `NewsItem[]` |

### Evaluator

| Method | Endpoint | Body/Params | Response |
|--------|----------|-------------|----------|
| `POST` | `/api/evaluator/analyze` | `{company_name}` | `EvaluationResult` |
| `GET` | `/api/evaluator/history` | `?limit=20` | `EvaluationResult[]` |
| `GET` | `/api/evaluator/reference-companies` | - | `ReferenceCompany[]` |

### Newsletter

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| `POST` | `/api/newsletter/generate` | `{time_range_days, topics[], tone}` | `{subject, html}` |
| `POST` | `/api/newsletter/send` | `{html, recipient_email, subject}` | `{success, id}` |

---

## 10. Data Models & Scoring

### Database Tables (SQLite + async SQLAlchemy)

```
WatchlistItem
  - id: Integer (PK)
  - company_name: String (required)
  - ticker: String (optional)
  - added_at: DateTime (UTC)

CachedNewsItem
  - id: Integer (PK)
  - title: String
  - url: String (unique)
  - source: String
  - category: String
  - summary: String
  - image_url: String
  - published_at: DateTime
  - fetched_at: DateTime
  - raw_data: JSON

Evaluation
  - id: Integer (PK)
  - company_name: String
  - zone: String (dead/compression/adaptation/fortress)
  - overview: Text
  - justification: Text
  - diligence: JSON (string[])
  - x_score: Float (0-100)
  - y_score: Float (0-100)
  - created_at: DateTime (UTC)
```

### In-Memory Caches

| Cache | TTL | Location |
|-------|-----|----------|
| Stock prices | 15 min | `stock_client.py` |
| Arena rankings | 60 min | `arena_client.py` |
| News queries (Mediastack) | 30 min | `news_client.py` |
| Aggregated news items | 15 min (scheduler refresh) | `news_aggregator.py` |

---

## 11. Architecture

### Backend File Structure

```
backend/
  app/
    main.py                        # FastAPI app, lifespan, router registration
    config.py                      # Pydantic settings (env vars)
    database.py                    # Async SQLAlchemy engine + session
    models/
      db_models.py                 # WatchlistItem, CachedNewsItem, Evaluation
      schemas.py                   # Pydantic request/response schemas
    apis/
      stock_client.py              # yfinance wrapper (async)
      arena_client.py              # arena.ai scraper + static fallback
      claude_client.py             # Anthropic Claude (analyze, filter, newsletter)
      news_client.py               # Mediastack API
      twitter_client.py            # Twitter/X v2 API
      rss_client.py                # RSS/Atom feed parser (12 feeds)
      institutional_client.py      # Google News RSS proxy (tier-1 pubs)
      email_client.py              # Resend transactional email
    services/
      stock_service.py             # Basket indexing + time series
      arena_service.py             # Rankings + AI spend enrichment
      news_aggregator.py           # Multi-source merge, score, dedup
      evaluator_service.py         # Claude company analysis + DB cache
      newsletter_service.py        # Newsletter generation + delivery
      scheduler.py                 # APScheduler (15-min refresh)
    routers/
      stocks.py                    # /api/stocks/*
      arena.py                     # /api/arena/*
      news.py                      # /api/news/*
      watchlist.py                 # /api/watchlist/*
      evaluator.py                 # /api/evaluator/*
      newsletter.py                # /api/newsletter/*
      _deps.py                     # Dependency injection (service getters)
    seed/
      baskets.py                   # Stock tickers by zone (5 baskets)
      ai_spend.py                  # 2026 AI capex/raised figures
      zone_companies.py            # 12 reference companies for matrix
```

### Frontend File Structure

```
frontend/
  src/
    App.tsx                        # React Router (4 routes)
    main.tsx                       # React 19 root render
    index.css                      # Tailwind + custom styles
    types/
      index.ts                     # TypeScript interfaces
    utils/
      format.ts                    # Date, number, currency formatters
    hooks/
      useApi.ts                    # Generic POST/PUT/DELETE hook
      usePolling.ts                # Auto-refresh polling hook
    pages/
      Home.tsx                     # 3-column dashboard
      Evaluator.tsx                # AI company analysis
      Watchlist.tsx                # Company watchlist CRUD
      Newsletter.tsx               # Newsletter generator
    components/
      Layout.tsx                   # Nav bar + routing
      BasketChart.tsx              # Stock index line chart (Recharts)
      BasketLegend.tsx             # Zone summary cards
      ArenaChart.tsx               # LLM Elo bar chart (custom)
      NewsFeed.tsx                 # Left panel news list
      NewsCard.tsx                 # Individual news item card
      SourceBadge.tsx              # Colored source badges
      FundraisingTable.tsx         # Compact fundraising list
      MatrixChart.tsx              # Interactive 2x2 SVG matrix
      CompanyOverview.tsx          # Multi-paragraph text
      VulnerabilityCard.tsx        # Zone + scores + justification
      DiligenceList.tsx            # Numbered checklist
      WatchlistPanel.tsx           # Expandable company card
      NewsletterEditor.tsx         # HTML preview + email send
```

### External API Keys

| Key | Service | Required |
|-----|---------|----------|
| `ANTHROPIC_API_KEY` | Claude AI (evaluator, news filter, newsletter) | Yes (core feature) |
| `MEDIASTACK_KEY` | News API (free tier) | Optional |
| `TWITTER_BEARER_TOKEN` | Twitter/X v2 | Optional (graceful fallback) |
| `RESEND_API_KEY` | Transactional email | Optional (newsletter send only) |

### Ports

| Service | Port |
|---------|------|
| FastAPI backend | 8006 |
| Vite dev server | 5173 |
| Vite proxy (`/api`) | -> localhost:8006 |
