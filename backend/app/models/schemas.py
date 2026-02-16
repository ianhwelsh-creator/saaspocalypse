"""Pydantic request/response schemas."""

from datetime import datetime
from pydantic import BaseModel


# --- Stocks ---

class StockDetail(BaseModel):
    ticker: str
    name: str
    current_price: float
    change_pct: float

class BasketDataPoint(BaseModel):
    date: str
    dead_zone: float | None = None
    compression_zone: float | None = None
    adaptation_zone: float | None = None
    fortress_zone: float | None = None
    ai_etfs: float | None = None

class BasketSummary(BaseModel):
    zone: str
    current_value: float
    change_from_baseline: float
    color: str
    tickers: list[str]

class BasketTimeSeriesResponse(BaseModel):
    series: list[BasketDataPoint]
    summaries: list[BasketSummary]
    baseline_date: str


# --- Arena ---

class ArenaModelResponse(BaseModel):
    rank: int
    model_name: str
    elo_score: float
    organization: str
    ai_spend_billions: float | None = None


# --- News ---

class NewsItemResponse(BaseModel):
    id: int | None = None
    title: str
    url: str
    source: str
    category: str | None = None
    summary: str | None = None
    image_url: str | None = None
    published_at: datetime


# --- Watchlist ---

class WatchlistItemCreate(BaseModel):
    company_name: str
    ticker: str | None = None

class WatchlistItemResponse(BaseModel):
    id: int
    company_name: str
    ticker: str | None = None
    added_at: datetime


# --- Evaluator ---

class EvaluationRequest(BaseModel):
    company_name: str

class ReferenceCompany(BaseModel):
    name: str
    ticker: str
    zone: str
    x: float
    y: float
    bullets: list[str]
    logo_url: str | None = None

class EvaluationResponse(BaseModel):
    id: int | None = None
    company_name: str
    zone: str
    overview: str
    justification: str
    diligence: list[str]
    x_score: float
    y_score: float
    created_at: datetime | None = None


# --- Cohorts ---

class CohortCreateRequest(BaseModel):
    name: str
    company_names: list[str]

class CohortSummaryResponse(BaseModel):
    id: int
    name: str
    status: str
    total_companies: int
    completed_companies: int
    current_company: str | None = None
    created_at: datetime

class CohortMemberSummary(BaseModel):
    evaluation_id: int
    company_name: str
    zone: str
    x_score: float
    y_score: float
    key_risk: str
    ai_summary: str

class CohortDetailResponse(CohortSummaryResponse):
    members: list[CohortMemberSummary] = []

class CohortEditRequest(BaseModel):
    add_companies: list[str] = []
    remove_evaluation_ids: list[int] = []


# --- Newsletter ---

class NewsletterRequest(BaseModel):
    time_range_days: int = 7
    topics: list[str] = []
    tone: str = "professional"

class NewsletterPreview(BaseModel):
    subject: str
    html: str

class SendEmailRequest(BaseModel):
    html: str
    recipient_email: str
    subject: str
