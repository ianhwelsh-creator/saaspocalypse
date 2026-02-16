"""Stock baskets API endpoints."""

from fastapi import APIRouter, Depends

from app.routers._deps import get_stock_client
from app.services.stock_service import StockService

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/baskets")
async def get_baskets(end_date: str | None = None):
    """Get indexed time series for all baskets since SaaSpocalypse baseline."""
    client = get_stock_client()
    service = StockService(client)
    return await service.get_basket_time_series(end_date=end_date)


@router.get("/baskets/{zone}")
async def get_basket_detail(zone: str):
    """Get individual stock details for a specific zone."""
    client = get_stock_client()
    service = StockService(client)
    return await service.get_basket_detail(zone)
