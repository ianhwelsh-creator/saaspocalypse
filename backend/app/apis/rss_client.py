"""RSS/Atom feed scraper using feedparser. No API keys required.

All news sources are consumed as RSS feeds:
  - Hacker News (top/best filtered via hnrss.org)
  - TechCrunch AI category
  - Reddit r/SaaS and r/LocalLLaMA (hot, not new)
  - Substacks and tech blogs
"""

import asyncio
import html
import logging
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser

logger = logging.getLogger(__name__)

# ── Feed registry ────────────────────────────────────────────────────────────

FEEDS: list[dict] = [
    # Hacker News — top-voted SaaS stories (points > 5 filters noise)
    {
        "url": "https://hnrss.org/newest?q=SaaS&points=5",
        "name": "Hacker News",
        "source_tag": "hackernews",
    },
    {
        "url": "https://hnrss.org/newest?q=AI+SaaS&points=3",
        "name": "Hacker News",
        "source_tag": "hackernews",
    },
    {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "name": "TechCrunch AI",
        "source_tag": "techcrunch",
    },
    # Reddit — "hot" instead of "new" to surface popular posts
    {
        "url": "https://www.reddit.com/r/SaaS/hot/.rss?limit=25",
        "name": "r/SaaS",
        "source_tag": "reddit",
    },
    {
        "url": "https://www.reddit.com/r/LocalLLaMA/hot/.rss?limit=25",
        "name": "r/LocalLLaMA",
        "source_tag": "reddit",
    },
    {
        "url": "https://www.reddit.com/r/artificial/hot/.rss?limit=15",
        "name": "r/artificial",
        "source_tag": "reddit",
    },
    {
        "url": "https://www.reddit.com/r/singularity/hot/.rss?limit=15",
        "name": "r/singularity",
        "source_tag": "reddit",
    },
    # Substacks / blogs
    {
        "url": "https://tscsw.substack.com/feed",
        "name": "Don't Short SaaS",
        "source_tag": "rss",
    },
    {
        "url": "https://stratechery.com/feed/",
        "name": "Stratechery",
        "source_tag": "rss",
    },
    {
        "url": "https://blog.pragmaticengineer.com/rss/",
        "name": "Pragmatic Engineer",
        "source_tag": "rss",
    },
    {
        "url": "https://www.techmeme.com/feed.xml",
        "name": "Techmeme",
        "source_tag": "rss",
    },
    {
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "name": "Ars Technica",
        "source_tag": "rss",
    },
    {
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "name": "The Verge AI",
        "source_tag": "rss",
    },
    # ── New high-signal feeds (Feb 2026) ──────────────────────────────────
    # Priority sources (user-requested)
    {
        "url": "https://tomtunguz.com/index.xml",
        "name": "Tomasz Tunguz",
        "source_tag": "rss",
    },
    {
        "url": "https://thesaasplaybook.substack.com/feed",
        "name": "The SaaS Playbook",
        "source_tag": "rss",
    },
    {
        "url": "https://theainewsdigest.substack.com/feed",
        "name": "AI News Digest",
        "source_tag": "rss",
    },
    # Additional high-value Substacks & blogs
    {
        "url": "https://www.lennysnewsletter.com/feed",
        "name": "Lenny's Newsletter",
        "source_tag": "rss",
    },
    {
        "url": "https://www.notboring.co/feed",
        "name": "Not Boring",
        "source_tag": "rss",
    },
    {
        "url": "https://www.saastr.com/feed/",
        "name": "SaaStr",
        "source_tag": "rss",
    },
    {
        "url": "https://generalist.substack.com/feed",
        "name": "The Generalist",
        "source_tag": "rss",
    },
    {
        "url": "https://www.oneusefulthing.org/feed",
        "name": "One Useful Thing",
        "source_tag": "rss",
    },
    {
        "url": "https://simonwillison.net/atom/everything/",
        "name": "Simon Willison",
        "source_tag": "rss",
    },
    {
        "url": "https://www.newcomer.co/feed",
        "name": "Newcomer",
        "source_tag": "rss",
    },
    # Community
    {
        "url": "https://www.reddit.com/r/ChatGPT/hot/.rss?limit=15",
        "name": "r/ChatGPT",
        "source_tag": "reddit",
    },
]

# User-Agent header so Reddit doesn't 429 us
_USER_AGENT = "SaaSpocalypse/1.0 (feedparser; +https://github.com/saaspocalypse)"

# Regex to strip HTML tags from summaries
_TAG_RE = re.compile(r"<[^>]+>")

# Pattern to extract HN points from hnrss descriptions (e.g. "Comments: 12 | Points: 87")
_HN_POINTS_RE = re.compile(r"Points:\s*(\d+)", re.IGNORECASE)
_HN_COMMENTS_RE = re.compile(r"Comments:\s*(\d+)", re.IGNORECASE)

# Pattern to extract Reddit score from Atom feed content
_REDDIT_SCORE_RE = re.compile(r"submitted.*?(\d+)\s*(?:points|upvotes)", re.IGNORECASE)


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    return html.unescape(_TAG_RE.sub("", text)).strip()


def _parse_date(entry: feedparser.FeedParserDict) -> str:
    """Best-effort ISO date from an RSS/Atom entry."""
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).isoformat()
            except Exception:
                pass
    # feedparser sometimes populates *_parsed as a time.struct_time
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def _extract_image(entry: feedparser.FeedParserDict) -> str | None:
    """Try to pull a thumbnail / image URL from the entry."""
    # media:thumbnail (common in Reddit Atom feeds)
    for mt in getattr(entry, "media_thumbnail", []):
        url = mt.get("url")
        if url and url.startswith("http"):
            return url
    # enclosures (podcasts / TechCrunch sometimes)
    for enc in getattr(entry, "enclosures", []):
        if enc.get("type", "").startswith("image"):
            return enc.get("href")
    return None


def _extract_engagement(entry: feedparser.FeedParserDict, source_tag: str) -> dict:
    """Extract platform-specific engagement metrics from RSS entry metadata."""
    metrics: dict = {}

    if source_tag == "hackernews":
        # hnrss.org embeds points and comments in the description
        raw = entry.get("summary", "") or ""
        m = _HN_POINTS_RE.search(raw)
        if m:
            metrics["points"] = int(m.group(1))
        m = _HN_COMMENTS_RE.search(raw)
        if m:
            metrics["comments"] = int(m.group(1))

    elif source_tag == "reddit":
        # Reddit Atom feeds sometimes include score in content
        raw = ""
        if hasattr(entry, "content") and entry.content:
            raw = entry.content[0].get("value", "")
        if not raw:
            raw = entry.get("summary", "") or ""
        m = _REDDIT_SCORE_RE.search(raw)
        if m:
            metrics["score"] = int(m.group(1))

    return metrics


class RSSClient:
    """Async RSS client backed by feedparser.  Zero API keys required."""

    def __init__(
        self,
        feeds: list[dict] | None = None,
        cache_ttl_minutes: int = 15,
        items_per_feed: int = 25,
    ):
        self._feeds = feeds or FEEDS
        self._items_per_feed = items_per_feed
        self._cache: dict[str, tuple[list[dict], datetime]] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)

    # ── public ────────────────────────────────────────────────────────────

    async def fetch_feed(self, feed_url: str, feed_name: str, source_tag: str = "rss") -> list[dict]:
        """Parse one feed.  Returns a list of normalised news-item dicts."""
        cache_key = feed_url
        if cache_key in self._cache:
            data, ts = self._cache[cache_key]
            if datetime.now(timezone.utc) - ts < self._cache_ttl:
                return data

        try:
            # feedparser is synchronous — offload to the thread pool
            parsed = await asyncio.to_thread(
                feedparser.parse,
                feed_url,
                agent=_USER_AGENT,
            )

            items: list[dict] = []
            for entry in parsed.entries[: self._items_per_feed]:
                title = entry.get("title", "").strip()
                if not title:
                    continue

                # Build summary: prefer content, fallback to summary field
                raw_summary = ""
                if hasattr(entry, "content") and entry.content:
                    raw_summary = entry.content[0].get("value", "")
                if not raw_summary:
                    raw_summary = entry.get("summary", "")
                summary = _strip_html(raw_summary)[:400]

                # Extract engagement metrics
                engagement = _extract_engagement(entry, source_tag)

                item = {
                    "title": title,
                    "url": entry.get("link", ""),
                    "source": source_tag,
                    "summary": summary,
                    "image_url": _extract_image(entry),
                    "published_at": _parse_date(entry),
                    "feed_name": feed_name,
                }

                # Attach engagement data if found
                if engagement:
                    item["engagement"] = engagement

                items.append(item)

            self._cache[cache_key] = (items, datetime.now(timezone.utc))
            logger.info(f"Fetched {len(items)} items from {feed_name}")
            return items

        except Exception as e:
            logger.error(f"RSS feed parse failed for {feed_name} ({feed_url}): {e}")
            return []

    async def fetch_all_feeds(self) -> list[dict]:
        """Fetch every configured feed concurrently and return the merged list."""
        tasks = [
            self.fetch_feed(f["url"], f["name"], f.get("source_tag", "rss"))
            for f in self._feeds
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: list[dict] = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Feed fetch raised: {result}")
        return all_items

    async def search_feeds_for_company(self, company_name: str) -> list[dict]:
        """Re-fetch HN with a company-specific query for watchlist lookups."""
        url = f"https://hnrss.org/newest?q={company_name}"
        return await self.fetch_feed(url, f"HN: {company_name}", "hackernews")

    async def close(self):
        pass  # nothing to tear down — feedparser is stateless
