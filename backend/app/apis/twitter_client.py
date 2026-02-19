"""Twitter/X API v2 client. Optional — gracefully skips if no bearer token.

Cost-optimised: 20 curated accounts, 4 API calls per refresh, 4-hour cache.
Basic tier ($200/mo) allows 15K tweet reads/month.
At 4 calls × ~18 tweets × 6 refreshes/day × 30 days ≈ 13K reads — under limit.
"""

import logging
from datetime import datetime, timezone, timedelta

import httpx

logger = logging.getLogger(__name__)

# ── Curated high-signal AI + SaaS accounts ────────────────────────────────────
# These are followed unconditionally (no keyword filter) — everything they post
# is worth surfacing.  4-hour cache keeps API costs under Basic tier limit.

CURATED_ACCOUNTS: list[dict] = [
    # AI Leaders / Execs
    {"handle": "sama", "display_name": "Sam Altman"},
    {"handle": "DarioAmodei", "display_name": "Dario Amodei"},
    {"handle": "demishassabis", "display_name": "Demis Hassabis"},
    {"handle": "satabordo", "display_name": "Satya Nadella"},
    # AI Researchers / Builders
    {"handle": "karpathy", "display_name": "Andrej Karpathy"},
    {"handle": "ylecun", "display_name": "Yann LeCun"},
    {"handle": "jimfan_", "display_name": "Jim Fan"},
    {"handle": "swabordo", "display_name": "Swami Sivasubramanian"},
    # Media / Shows
    {"handle": "tbpn", "display_name": "TBPN"},
    {"handle": "thisweekinai_", "display_name": "This Week in AI"},
    # Reporters
    {"handle": "EricNewcomer", "display_name": "Eric Newcomer"},
    {"handle": "karaswisher", "display_name": "Kara Swisher"},
    {"handle": "kylewiggers", "display_name": "Kyle Wiggers"},
    # VCs / Analysts
    {"handle": "ttunguz", "display_name": "Tomasz Tunguz"},
    {"handle": "jasonlk", "display_name": "Jason Lemkin"},
    {"handle": "benedictevans", "display_name": "Benedict Evans"},
    {"handle": "emabordo", "display_name": "Emad Mostaque"},
    # Labs / Orgs
    {"handle": "AnthropicAI", "display_name": "Anthropic"},
    {"handle": "OpenAI", "display_name": "OpenAI"},
    {"handle": "GoogleDeepMind", "display_name": "Google DeepMind"},
]


class TwitterClient:
    BASE_URL = "https://api.twitter.com/2"

    def __init__(self, bearer_token: str, cache_ttl_minutes: int = 240):
        self._bearer_token = bearer_token
        self._client = httpx.AsyncClient(timeout=15)
        self._cache: dict[str, tuple[list, datetime]] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)

    # ── Public API ─────────────────────────────────────────────────────────

    async def search_recent(self, query: str, max_results: int = 20) -> list[dict]:
        """Search recent tweets with author metadata. Returns empty list if no API key."""
        if not self._bearer_token:
            return []

        cache_key = f"twitter_{query}_{max_results}"
        if cache_key in self._cache:
            data, ts = self._cache[cache_key]
            if datetime.now(timezone.utc) - ts < self._cache_ttl:
                return data

        full_query = f"{query} -is:retweet lang:en"
        items = await self._search_with_users(full_query, max_results)
        self._cache[cache_key] = (items, datetime.now(timezone.utc))
        return items

    async def fetch_curated_accounts(self, max_per_account: int = 3) -> list[dict]:
        """Fetch recent tweets from curated high-signal accounts.

        Batches accounts into groups of 6 using OR queries to minimise API calls.
        20 accounts = 4 batches = 4 API calls.  4-hour cache keeps costs low.
        """
        if not self._bearer_token:
            return []

        cache_key = "twitter_curated_accounts"
        if cache_key in self._cache:
            data, ts = self._cache[cache_key]
            if datetime.now(timezone.utc) - ts < self._cache_ttl:
                return data

        all_tweets: list[dict] = []
        batch_size = 6

        for i in range(0, len(CURATED_ACCOUNTS), batch_size):
            batch = CURATED_ACCOUNTS[i : i + batch_size]
            from_clause = " OR ".join(f"from:{a['handle']}" for a in batch)
            query = f"({from_clause}) -is:retweet lang:en"

            tweets = await self._search_with_users(
                query, max_results=min(max_per_account * len(batch), 100)
            )
            all_tweets.extend(tweets)

        logger.info(f"Curated tweets: fetched {len(all_tweets)} from {len(CURATED_ACCOUNTS)} accounts")
        self._cache[cache_key] = (all_tweets, datetime.now(timezone.utc))
        return all_tweets

    async def close(self):
        await self._client.aclose()

    # ── Internal ───────────────────────────────────────────────────────────

    async def _search_with_users(self, query: str, max_results: int = 20) -> list[dict]:
        """Search tweets with author expansion (username, name, profile image)."""
        try:
            resp = await self._client.get(
                f"{self.BASE_URL}/tweets/search/recent",
                params={
                    "query": query,
                    "max_results": min(max(max_results, 10), 100),
                    "tweet.fields": "created_at,author_id,public_metrics",
                    "expansions": "author_id",
                    "user.fields": "username,name,profile_image_url",
                },
                headers={"Authorization": f"Bearer {self._bearer_token}"},
            )
            resp.raise_for_status()
            payload = resp.json()
            tweets = payload.get("data", [])

            # Build author lookup from includes.users
            users = {u["id"]: u for u in payload.get("includes", {}).get("users", [])}

            items: list[dict] = []
            for t in tweets:
                metrics = t.get("public_metrics", {})
                author = users.get(t.get("author_id", ""), {})
                username = author.get("username", "")

                items.append({
                    "title": t.get("text", "")[:140],
                    "url": f"https://twitter.com/{username or 'i'}/status/{t.get('id', '')}",
                    "source": "twitter",
                    "summary": t.get("text", ""),
                    "image_url": None,
                    "published_at": t.get("created_at", ""),
                    "engagement": {
                        "likes": metrics.get("like_count", 0),
                        "retweets": metrics.get("retweet_count", 0),
                        "replies": metrics.get("reply_count", 0),
                        "impressions": metrics.get("impression_count", 0),
                    },
                    # Author metadata (new)
                    "author_username": username,
                    "author_display_name": author.get("name", ""),
                    "author_profile_image": author.get("profile_image_url", ""),
                })

            return items
        except httpx.HTTPError as e:
            logger.error(f"Twitter search failed: {e}")
            return []
