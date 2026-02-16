"""News aggregation API endpoints."""

from fastapi import APIRouter

from app.routers._deps import get_news_aggregator

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
async def get_news(
    category: str | None = None,
    source: str | None = None,
    content_type: str | None = None,
    sort: str = "score",
    limit: int = 50,
    offset: int = 0,
):
    """Get aggregated news feed from all sources, ranked by composite score."""
    aggregator = get_news_aggregator()
    return await aggregator.get_all_news(
        category=category, source=source, content_type=content_type,
        sort=sort, limit=limit, offset=offset,
    )


@router.get("/fundraising")
async def get_fundraising_news(limit: int = 20):
    """Get fundraising-specific news."""
    aggregator = get_news_aggregator()
    return await aggregator.get_fundraising_news(limit=limit)
