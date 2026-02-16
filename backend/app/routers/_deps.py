"""Shared dependency accessors for routers. Set by main.py at startup."""

from app.apis.stock_client import StockClient
from app.apis.claude_client import ClaudeClient
from app.services.arena_service import ArenaService
from app.services.news_aggregator import NewsAggregator
from app.services.newsletter_service import NewsletterService
from app.services.cohort_service import CohortService

_stock_client: StockClient | None = None
_claude_client: ClaudeClient | None = None
_arena_service: ArenaService | None = None
_news_aggregator: NewsAggregator | None = None
_newsletter_service: NewsletterService | None = None
_cohort_service: CohortService | None = None


def init_deps(
    stock_client: StockClient,
    claude_client: ClaudeClient | None = None,
    arena_service: ArenaService | None = None,
    news_aggregator: NewsAggregator | None = None,
    newsletter_service: NewsletterService | None = None,
    cohort_service: CohortService | None = None,
):
    global _stock_client, _claude_client, _arena_service, _news_aggregator, _newsletter_service, _cohort_service
    _stock_client = stock_client
    _claude_client = claude_client
    _arena_service = arena_service
    _news_aggregator = news_aggregator
    _newsletter_service = newsletter_service
    _cohort_service = cohort_service


def get_stock_client() -> StockClient:
    assert _stock_client is not None, "Stock client not initialized"
    return _stock_client


def get_claude_client() -> ClaudeClient | None:
    return _claude_client


def get_arena_service() -> ArenaService:
    assert _arena_service is not None, "Arena service not initialized"
    return _arena_service


def get_news_aggregator() -> NewsAggregator:
    assert _news_aggregator is not None, "News aggregator not initialized"
    return _news_aggregator


def get_newsletter_service() -> NewsletterService | None:
    return _newsletter_service


def get_cohort_service() -> CohortService | None:
    return _cohort_service
