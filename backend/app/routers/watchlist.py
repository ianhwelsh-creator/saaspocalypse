"""Watchlist CRUD API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import WatchlistItem
from app.models.schemas import WatchlistItemCreate, WatchlistItemResponse
from app.routers._deps import get_news_aggregator

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItemResponse])
async def list_watchlist(db: AsyncSession = Depends(get_db)):
    """Get all watched companies."""
    stmt = select(WatchlistItem).order_by(WatchlistItem.added_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=WatchlistItemResponse)
async def add_to_watchlist(item: WatchlistItemCreate, db: AsyncSession = Depends(get_db)):
    """Add a company to the watchlist."""
    watchlist_item = WatchlistItem(
        company_name=item.company_name,
        ticker=item.ticker,
    )
    db.add(watchlist_item)
    await db.commit()
    await db.refresh(watchlist_item)
    return watchlist_item


@router.delete("/{item_id}")
async def remove_from_watchlist(item_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a company from the watchlist."""
    stmt = select(WatchlistItem).where(WatchlistItem.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    await db.delete(item)
    await db.commit()
    return {"ok": True}


@router.get("/{item_id}/news")
async def get_watchlist_news(item_id: int, db: AsyncSession = Depends(get_db)):
    """Get recent news for a watched company."""
    stmt = select(WatchlistItem).where(WatchlistItem.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    aggregator = get_news_aggregator()
    return await aggregator.search_news_for_company(item.company_name)
