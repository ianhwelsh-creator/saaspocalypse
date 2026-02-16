"""Reddit API client for SaaS/AI subreddit posts."""

import logging
from datetime import datetime, timezone, timedelta

import httpx

logger = logging.getLogger(__name__)

SUBREDDITS = ["SaaS", "artificial", "technology", "singularity", "MachineLearning"]


class RedditClient:
    AUTH_URL = "https://www.reddit.com/api/v1/access_token"
    BASE_URL = "https://oauth.reddit.com"

    def __init__(self, client_id: str, client_secret: str, cache_ttl_minutes: int = 15):
        self._client_id = client_id
        self._client_secret = client_secret
        self._client = httpx.AsyncClient(timeout=15)
        self._token: str | None = None
        self._token_expires: datetime | None = None
        self._cache: dict[str, tuple[list, datetime]] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)

    async def _ensure_token(self):
        if self._token and self._token_expires and datetime.now(timezone.utc) < self._token_expires:
            return

        if not self._client_id or not self._client_secret:
            return

        try:
            resp = await self._client.post(
                self.AUTH_URL,
                auth=(self._client_id, self._client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": "SaaSpocalypse/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600) - 60)
        except Exception as e:
            logger.error(f"Reddit auth failed: {e}")

    async def get_posts(self, subreddit: str, limit: int = 10) -> list[dict]:
        """Fetch hot posts from a subreddit."""
        if not self._client_id:
            return []

        cache_key = f"reddit_{subreddit}_{limit}"
        if cache_key in self._cache:
            data, ts = self._cache[cache_key]
            if datetime.now(timezone.utc) - ts < self._cache_ttl:
                return data

        await self._ensure_token()
        if not self._token:
            return []

        try:
            resp = await self._client.get(
                f"{self.BASE_URL}/r/{subreddit}/hot",
                params={"limit": limit},
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "User-Agent": "SaaSpocalypse/1.0",
                },
            )
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])

            items = []
            for p in posts:
                d = p.get("data", {})
                if d.get("stickied"):
                    continue
                items.append({
                    "title": d.get("title", ""),
                    "url": f"https://reddit.com{d.get('permalink', '')}",
                    "source": "reddit",
                    "summary": (d.get("selftext", "") or "")[:300],
                    "image_url": d.get("thumbnail") if d.get("thumbnail", "").startswith("http") else None,
                    "published_at": datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).isoformat(),
                    "subreddit": subreddit,
                    "score": d.get("score", 0),
                })

            self._cache[cache_key] = (items, datetime.now(timezone.utc))
            return items
        except httpx.HTTPError as e:
            logger.error(f"Reddit fetch for r/{subreddit} failed: {e}")
            return []

    async def get_all_posts(self, limit_per_sub: int = 10) -> list[dict]:
        """Fetch posts from all configured subreddits."""
        all_posts = []
        for sub in SUBREDDITS:
            posts = await self.get_posts(sub, limit_per_sub)
            all_posts.extend(posts)
        return all_posts

    async def close(self):
        await self._client.aclose()
