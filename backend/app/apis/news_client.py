"""Mediastack API client for mainstream tech/AI/SaaS news.

Docs: https://mediastack.com/documentation
Free tier: 500 requests/month, access_key auth via query param.
NOTE: Free tier requires HTTP (not HTTPS).
"""

import logging
from datetime import datetime, timezone, timedelta

import httpx

logger = logging.getLogger(__name__)


class NewsApiClient:
    # Free tier only supports HTTP
    BASE_URL = "http://api.mediastack.com/v1"

    def __init__(self, api_key: str, cache_ttl_minutes: int = 30):
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=15)
        self._cache: dict[str, tuple[list, datetime]] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)

    def _is_cached(self, key: str) -> bool:
        if key not in self._cache:
            return False
        _, ts = self._cache[key]
        return datetime.now(timezone.utc) - ts < self._cache_ttl

    async def search_news(self, query: str, page_size: int = 20) -> list[dict]:
        """Search for news articles matching query via Mediastack."""
        if not self._api_key:
            logger.warning("Mediastack key not set, skipping")
            return []

        cache_key = f"mediastack_{query}_{page_size}"
        if self._is_cached(cache_key):
            return self._cache[cache_key][0]

        try:
            resp = await self._client.get(
                f"{self.BASE_URL}/news",
                params={
                    "access_key": self._api_key,
                    "keywords": query,
                    "languages": "en",
                    "sort": "published_desc",
                    "limit": min(page_size, 100),
                },
            )
            resp.raise_for_status()
            data = resp.json()

            if "error" in data:
                logger.error(f"Mediastack API error: {data['error']}")
                return []

            articles = data.get("data", [])

            items = []
            for a in articles:
                title = a.get("title", "")
                if not title:
                    continue
                items.append({
                    "title": title,
                    "url": a.get("url", ""),
                    "source": "newsapi",
                    "summary": a.get("description", ""),
                    "image_url": a.get("image"),
                    "published_at": a.get("published_at", ""),
                })

            self._cache[cache_key] = (items, datetime.now(timezone.utc))
            logger.info(f"Mediastack: fetched {len(items)} articles for '{query}'")
            return items
        except httpx.HTTPError as e:
            logger.error(f"Mediastack request failed: {e}")
            return []

    async def close(self):
        await self._client.aclose()
