"""News aggregation service — merges, scores, and deduplicates from all sources.

Scoring formula:
  score = relevance_score + popularity_score + source_authority + recency_bonus

  - relevance_score (0-40):  keyword hits in title/summary for SaaS/AI disruption
  - popularity_score (0-30): normalized engagement (HN points, Reddit upvotes, tweet likes)
  - source_authority (0-20):  editorial weight per source (Stratechery > random RSS)
  - recency_bonus   (0-10): exponential decay, full points within 2h, halves per 6h
"""

import logging
import math
from datetime import datetime, timezone, timedelta

from rapidfuzz import fuzz

from app.apis.twitter_client import TwitterClient
from app.apis.rss_client import RSSClient
from app.apis.institutional_client import InstitutionalClient

logger = logging.getLogger(__name__)

# ── Scoring constants ────────────────────────────────────────────────────────

# Source authority tiers (out of 20)
SOURCE_AUTHORITY: dict[str, int] = {
    # Tier 0 — institutional / paywalled (highest authority)
    "Wall Street Journal": 20,
    "Reuters": 19,
    "Financial Times": 19,
    "Bloomberg": 18,
    "CNBC": 16,
    "Institutional": 17,
    # Tier 1 — curated editorial, high signal
    "Stratechery": 20,
    "Techmeme": 18,
    "Don't Short SaaS": 18,
    "Pragmatic Engineer": 17,
    # Tier 2 — major tech news
    "TechCrunch AI": 16,
    "Ars Technica": 14,
    "The Verge AI": 14,
    # Tier 3 — community-driven (scored by engagement instead)
    "Hacker News": 12,
    "r/SaaS": 10,
    "r/LocalLLaMA": 10,
    "r/artificial": 9,
    "r/singularity": 9,
    "r/ChatGPT": 9,
    "r/MachineLearning": 12,
    "r/OpenAI": 10,
    "r/ClaudeAI": 10,
    "r/startups": 9,
    "r/technology": 8,
    # New feeds (Feb 2026)
    "Tomasz Tunguz": 20,
    "The SaaS Playbook": 18,
    "AI News Digest": 16,
    "Lenny's Newsletter": 17,
    "Not Boring": 16,
    "SaaStr": 17,
    "The Generalist": 15,
    "One Useful Thing": 16,
    "Simon Willison": 16,
    "Newcomer": 18,
    # Podcasts
    "Dwarkesh Patel": 19,
    "TBPN": 18,
    "Prof G Markets": 17,
    "Invest Like the Best": 18,
    "Capital Allocators": 17,
}
DEFAULT_AUTHORITY = 8


# ── Content type classification ──────────────────────────────────────────────

LONG_FORM_SOURCES = {"rss", "techcrunch"}
LONG_FORM_INSTITUTIONAL = {"wsj", "reuters", "ft", "bloomberg", "cnbc", "institutional"}
SHORT_FORM_SOURCES = {"twitter", "reddit", "hackernews", "podcast"}


def _classify_content_type(item: dict) -> str:
    """Classify item as 'long_form' or 'short_form' based on source."""
    source = item.get("source", "")
    if source in LONG_FORM_INSTITUTIONAL:
        return "long_form"
    if source in SHORT_FORM_SOURCES:
        return "short_form"
    if source in LONG_FORM_SOURCES:
        return "long_form"
    return "long_form"

# Relevance keywords and weights
RELEVANCE_KEYWORDS: list[tuple[list[str], int]] = [
    # High-value SaaS disruption terms (8 pts each)
    (["saas disruption", "saas dead", "replacing saas", "saas collapse",
      "ai replacing", "ai agent", "ai-native", "ai native"], 8),
    # Core SaaS/AI intersection (5 pts)
    (["saas", "software-as-a-service", "b2b software", "enterprise software",
      "seat-based", "per-seat", "subscription software"], 5),
    # AI & LLM terms (4 pts)
    (["artificial intelligence", "machine learning", "large language model",
      "llm", "gpt", "claude", "gemini", "copilot", "foundation model",
      "frontier model", "ai startup"], 4),
    # Business impact (3 pts)
    (["revenue compression", "margin pressure", "churn", "displacement",
      "market share", "disruption", "competitive moat", "pricing power"], 3),
    # General tech relevance (1 pt)
    (["funding", "acquisition", "ipo", "earnings", "valuation",
      "open source", "developer tools", "cloud"], 1),
]


def _compute_relevance(title: str, summary: str) -> int:
    """Score 0-40 based on keyword density in title + summary."""
    text = f"{title} {summary}".lower()
    score = 0
    for keywords, weight in RELEVANCE_KEYWORDS:
        for kw in keywords:
            if kw in text:
                score += weight
                break  # only count each tier once
    return min(score, 40)


def _compute_popularity(item: dict) -> int:
    """Score 0-30 based on engagement metrics from the source platform."""
    eng = item.get("engagement", {})
    source = item.get("source", "")

    if source == "hackernews":
        points = eng.get("points", 0)
        comments = eng.get("comments", 0)
        # HN: 100+ points is very popular, 500+ is viral
        raw = points + (comments * 0.5)
        return min(int(raw / 10), 30)

    if source == "reddit":
        score = eng.get("score", item.get("score", 0))
        # Reddit: 100+ upvotes is hot, 1000+ is viral
        if score > 0:
            return min(int(math.log2(max(score, 1)) * 3), 30)
        return 0

    if source == "twitter":
        likes = eng.get("likes", 0)
        retweets = eng.get("retweets", 0)
        # Twitter: likes + retweets weighted
        raw = likes + (retweets * 3)
        if raw > 0:
            return min(int(math.log2(max(raw, 1)) * 3), 30)
        return 0

    # Editorial sources — give a base popularity for being published at all
    if source in ("techcrunch", "rss"):
        return 5

    # Podcasts — base popularity for being a curated show
    if source == "podcast":
        return 8

    return 0


def _compute_recency(published_at: str) -> int:
    """Score 0-10 based on how recent the article is. Exponential decay."""
    try:
        if published_at.endswith("Z"):
            published_at = published_at[:-1] + "+00:00"
        pub = datetime.fromisoformat(published_at)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return 0

    hours_ago = (datetime.now(timezone.utc) - pub).total_seconds() / 3600

    if hours_ago < 0:
        return 10  # future-dated (clock skew)
    if hours_ago <= 2:
        return 10
    if hours_ago <= 6:
        return 8
    if hours_ago <= 12:
        return 6
    if hours_ago <= 24:
        return 4
    if hours_ago <= 48:
        return 2
    return 0


def _score_item(item: dict) -> int:
    """Compute composite score (0-100) for a news item."""
    relevance = _compute_relevance(
        item.get("title", ""),
        item.get("summary", ""),
    )
    popularity = _compute_popularity(item)
    authority = SOURCE_AUTHORITY.get(item.get("feed_name", ""), DEFAULT_AUTHORITY)
    recency = _compute_recency(item.get("published_at", ""))

    return relevance + popularity + authority + recency


class NewsAggregator:
    def __init__(
        self,
        rss_client: RSSClient,
        twitter_client: TwitterClient,
        institutional_client: InstitutionalClient | None = None,
        claude_client=None,
    ):
        self._rss = rss_client
        self._twitter = twitter_client
        self._institutional = institutional_client
        self._claude = claude_client
        self._cached_all: list[dict] = []
        self._cached_fundraising: list[dict] = []

    async def get_all_news(
        self, category: str | None = None, source: str | None = None,
        content_type: str | None = None,
        limit: int = 50, offset: int = 0, sort: str = "score",
    ) -> list[dict]:
        """Get aggregated news from all sources, scored and deduplicated."""
        if not self._cached_all:
            await self.refresh_news()

        items = self._cached_all

        if category:
            items = [i for i in items if i.get("category") == category]
        if source:
            items = [i for i in items if i.get("source") == source]
        if content_type:
            items = [i for i in items if i.get("content_type") == content_type]

        # Re-sort based on requested order
        if sort == "recent":
            items = sorted(items, key=lambda x: x.get("published_at", ""), reverse=True)
        # default is already sorted by score from refresh_news()

        return items[offset : offset + limit]

    async def get_fundraising_news(self, limit: int = 20) -> list[dict]:
        """Get fundraising-specific news."""
        if not self._cached_fundraising:
            await self.refresh_fundraising()
        return self._cached_fundraising[:limit]

    async def search_news_for_company(self, company_name: str, limit: int = 20) -> list[dict]:
        """Search for news about a specific company (watchlist feature)."""
        results: list[dict] = []

        # Free: HN search via hnrss.org
        hn_items = await self._rss.search_feeds_for_company(company_name)
        results.extend(hn_items)

        for item in results:
            item["category"] = self._categorize(item.get("title", ""))
            item["score"] = _score_item(item)

        results = self._deduplicate(results)
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:limit]

    async def refresh_news(self):
        """Refresh all news sources, score, merge, and sort."""
        all_items: list[dict] = []

        # ── Institutional FIRST (wins dedup over community sources) ──────
        # Added first so they survive deduplication against RSS/community
        if self._institutional:
            try:
                raw_institutional = await self._institutional.fetch_institutional_news()
                logger.info(f"Raw institutional items: {len(raw_institutional)}")

                # Run through Claude filter if available
                if self._claude and raw_institutional:
                    try:
                        filtered = await self._claude.filter_institutional_news(raw_institutional)
                        # Apply Claude's AI relevance score as a bonus to the item
                        for item in filtered:
                            ai_score = item.get("ai_relevance_score", 0)
                            # Boost items that Claude rated highly
                            if ai_score >= 90:
                                item["_ai_bonus"] = 15
                            elif ai_score >= 75:
                                item["_ai_bonus"] = 10
                            else:
                                item["_ai_bonus"] = 5
                        all_items.extend(filtered)
                        logger.info(f"Claude-filtered institutional items: {len(filtered)}")
                    except Exception as e:
                        logger.error(f"Claude filtering failed, using raw items: {e}")
                        all_items.extend(raw_institutional)
                else:
                    all_items.extend(raw_institutional)
            except Exception as e:
                logger.error(f"Institutional news fetch failed: {e}")

        # ── Free: RSS feeds (HN, TechCrunch, Reddit, Substacks, blogs, podcasts) ──
        rss_items = await self._rss.fetch_all_feeds()
        all_items.extend(rss_items)

        # ── Paid/optional: Twitter/X (cost-optimised) ──────────────────
        # Only curated accounts — keyword search dropped to save API reads.
        # 6 accounts × 3 tweets = ~18 tweets, 1 API call, 60-min cache.
        curated_tweets = await self._twitter.fetch_curated_accounts()
        all_items.extend(curated_tweets)

        # Categorize all items
        for item in all_items:
            if not item.get("category"):
                item["category"] = self._categorize(item.get("title", ""))

        # Deduplicate
        all_items = self._deduplicate(all_items)

        # Score every item
        for item in all_items:
            item["score"] = _score_item(item)
            # Apply AI bonus from Claude filter (institutional items)
            ai_bonus = item.pop("_ai_bonus", 0)
            if ai_bonus:
                item["score"] = min(item["score"] + ai_bonus, 100)

        # Classify content type (long-form articles vs short-form quick hits)
        for item in all_items:
            item["content_type"] = _classify_content_type(item)

        # Sort by score descending (highest relevance+popularity first)
        all_items.sort(key=lambda x: x.get("score", 0), reverse=True)

        self._cached_all = all_items
        logger.info(
            f"News refresh complete: {len(all_items)} items "
            f"(top score: {all_items[0].get('score', 0) if all_items else 0})"
        )

    async def refresh_fundraising(self):
        """Refresh fundraising-specific news."""
        items: list[dict] = []

        # Pull fundraising-tagged items from the main RSS cache
        if self._cached_all:
            for item in self._cached_all:
                if item.get("category") == "fundraising":
                    items.append(item)

        items = self._deduplicate(items)

        # Score and sort
        for item in items:
            if "score" not in item:
                item["score"] = _score_item(item)
        items.sort(key=lambda x: x.get("score", 0), reverse=True)

        self._cached_fundraising = items

    def _deduplicate(self, items: list[dict]) -> list[dict]:
        """Remove duplicate articles by title similarity."""
        seen: list[str] = []
        unique: list[dict] = []

        for item in items:
            title = item.get("title", "")
            if not title:
                continue
            is_dup = False
            for seen_title in seen:
                if fuzz.ratio(title.lower(), seen_title.lower()) > 80:
                    is_dup = True
                    break
            if not is_dup:
                seen.append(title)
                unique.append(item)

        return unique

    def _categorize(self, title: str) -> str:
        """Simple keyword-based categorization."""
        t = title.lower()
        if any(w in t for w in ["funding", "raised", "series", "ipo", "bond", "valuation"]):
            return "fundraising"
        if any(w in t for w in ["earnings", "revenue", "quarterly", "profit", "margin"]):
            return "earnings"
        if any(w in t for w in ["launch", "release", "announce", "new feature", "product"]):
            return "product_launch"
        return "ai_disruption"
