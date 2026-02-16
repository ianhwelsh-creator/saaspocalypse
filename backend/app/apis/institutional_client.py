"""Institutional news client — proxies WSJ, Reuters, FT via Google News RSS.

Google News aggregates paywalled sources and exposes them as RSS items.
We search for SaaS/AI/Cloud/Antitrust topics scoped to tier-1 publications,
then optionally run results through Claude for SaaSpocalypse-relevant filtering.
"""

import asyncio
import html
import logging
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import feedparser

logger = logging.getLogger(__name__)

# ── Google News RSS search queries ───────────────────────────────────────────

# Sites we want to proxy through Google News
INSTITUTIONAL_SITES = [
    "wsj.com",
    "reuters.com",
    "ft.com",
    "bloomberg.com",
    "cnbc.com",
]

# Topics relevant to SaaSpocalypse thesis
TOPIC_QUERIES = [
    "AI OR SaaS OR Antitrust OR Cloud",
    "artificial intelligence enterprise software",
    "AI startup funding",
]

_TAG_RE = re.compile(r"<[^>]+>")
_USER_AGENT = "SaaSpocalypse/1.0 (feedparser; +https://github.com/saaspocalypse)"


def _strip_html(text: str) -> str:
    return html.unescape(_TAG_RE.sub("", text)).strip()


def _infer_source(url: str, title: str, source_name: str = "") -> str:
    """Infer the original publication from the Google News item URL, title, or RSS source element.

    Google News RSS entries include a <source> element with the publisher name,
    and titles often end with " - Publisher Name".
    """
    # Combine all signals
    combined = f"{url} {title} {source_name}".lower()

    if "wsj.com" in combined or "wall street journal" in combined:
        return "wsj"
    if "reuters.com" in combined or "reuters" in combined:
        return "reuters"
    if "ft.com" in combined or "financial times" in combined:
        return "ft"
    if "bloomberg.com" in combined or "bloomberg" in combined:
        return "bloomberg"
    if "cnbc.com" in combined or "cnbc" in combined:
        return "cnbc"
    return "institutional"


def _parse_date(entry) -> str:
    """Extract ISO date from a Google News RSS entry."""
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).isoformat()
            except Exception:
                pass
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def _build_google_news_url(topic_query: str) -> str:
    """Build a Google News RSS search URL filtering to institutional sites."""
    site_filter = "+OR+".join(f"site:{s}" for s in INSTITUTIONAL_SITES)
    q = f"({site_filter})+AND+({topic_query})"
    return (
        f"https://news.google.com/rss/search?"
        f"q={quote(q, safe='+():')}&hl=en-US&gl=US&ceid=US:en"
    )


class InstitutionalClient:
    """Fetches institutional news (WSJ, Reuters, FT, etc.) via Google News RSS."""

    def __init__(self, cache_ttl_minutes: int = 30, items_per_query: int = 15):
        self._items_per_query = items_per_query
        self._cache: dict[str, tuple[list[dict], datetime]] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)

    async def fetch_institutional_news(self) -> list[dict]:
        """Fetch all institutional news across topic queries."""
        tasks = [self._fetch_query(q) for q in TOPIC_QUERIES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: list[dict] = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Institutional feed fetch error: {result}")

        # Deduplicate by URL
        seen_urls: set[str] = set()
        unique: list[dict] = []
        for item in all_items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(item)

        logger.info(f"Institutional news: {len(unique)} unique items from {len(all_items)} total")
        return unique

    async def _fetch_query(self, topic_query: str) -> list[dict]:
        """Fetch one Google News RSS query."""
        feed_url = _build_google_news_url(topic_query)
        cache_key = topic_query

        if cache_key in self._cache:
            data, ts = self._cache[cache_key]
            if datetime.now(timezone.utc) - ts < self._cache_ttl:
                return data

        try:
            parsed = await asyncio.to_thread(
                feedparser.parse,
                feed_url,
                agent=_USER_AGENT,
            )

            items: list[dict] = []
            for entry in parsed.entries[: self._items_per_query]:
                title = entry.get("title", "").strip()
                if not title:
                    continue

                # Google News often appends " - Source Name" to the title
                # We keep it as-is since it helps identify the source
                url = entry.get("link", "")
                # feedparser exposes <source> element as entry.source
                rss_source = ""
                if hasattr(entry, "source") and isinstance(entry.source, dict):
                    rss_source = entry.source.get("title", "")
                elif hasattr(entry, "source") and hasattr(entry.source, "title"):
                    rss_source = getattr(entry.source, "title", "")
                source = _infer_source(url, title, rss_source)

                raw_summary = entry.get("summary", "")
                summary = _strip_html(raw_summary)[:400] if raw_summary else ""

                item = {
                    "title": title,
                    "url": url,
                    "source": source,
                    "summary": summary,
                    "published_at": _parse_date(entry),
                    "feed_name": self._source_display_name(source),
                }
                items.append(item)

            self._cache[cache_key] = (items, datetime.now(timezone.utc))
            logger.info(f"Fetched {len(items)} institutional items for query: {topic_query[:40]}")
            return items

        except Exception as e:
            logger.error(f"Institutional fetch failed for '{topic_query[:40]}': {e}")
            return []

    @staticmethod
    def _source_display_name(source: str) -> str:
        return {
            "wsj": "Wall Street Journal",
            "reuters": "Reuters",
            "ft": "Financial Times",
            "bloomberg": "Bloomberg",
            "cnbc": "CNBC",
        }.get(source, "Institutional")

    async def close(self):
        pass  # stateless
