"""LLM Arena rankings API endpoint."""

from fastapi import APIRouter

from app.routers._deps import get_arena_service

router = APIRouter(prefix="/api/arena", tags=["arena"])


@router.get("/rankings")
async def get_rankings(top_n: int = 15):
    """Get top LLM arena model rankings with AI spend context."""
    service = get_arena_service()
    return await service.get_rankings_with_spend(top_n=top_n)
