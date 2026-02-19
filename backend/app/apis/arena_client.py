"""LLM Arena leaderboard data fetcher — arena.ai"""

import re
import logging
from datetime import datetime, timezone, timedelta

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Fallback static data — updated from https://arena.ai/leaderboard (Feb 2026)
STATIC_RANKINGS = [
    {"rank": 1, "model_name": "Claude Opus 4.6 (Thinking)", "elo_score": 1506, "organization": "Anthropic"},
    {"rank": 2, "model_name": "Claude Opus 4.6", "elo_score": 1502, "organization": "Anthropic"},
    {"rank": 3, "model_name": "Gemini 3 Pro", "elo_score": 1486, "organization": "Google"},
    {"rank": 4, "model_name": "Grok 4.1 (Thinking)", "elo_score": 1475, "organization": "xAI"},
    {"rank": 5, "model_name": "Gemini 3 Flash", "elo_score": 1473, "organization": "Google"},
    {"rank": 6, "model_name": "Claude Opus 4.5 (Thinking)", "elo_score": 1471, "organization": "Anthropic"},
    {"rank": 7, "model_name": "Claude Opus 4.5", "elo_score": 1467, "organization": "Anthropic"},
    {"rank": 8, "model_name": "Grok 4.1", "elo_score": 1464, "organization": "xAI"},
    {"rank": 9, "model_name": "Gemini 3 Flash (Thinking)", "elo_score": 1462, "organization": "Google"},
    {"rank": 10, "model_name": "GPT-5.1 High", "elo_score": 1457, "organization": "OpenAI"},
    {"rank": 11, "model_name": "Llama 4 Maverick", "elo_score": 1450, "organization": "Meta"},
    {"rank": 12, "model_name": "DeepSeek R2", "elo_score": 1444, "organization": "DeepSeek"},
]

# Org keywords that might appear as prefixes in scraped model names
ORG_PREFIXES = {
    "anthropic": "Anthropic",
    "google": "Google",
    "openai": "OpenAI",
    "meta": "Meta",
    "xai": "xAI",
    "deepseek": "DeepSeek",
    "mistral ai": "Mistral",
    "mistral": "Mistral",
    "microsoft": "Microsoft",
    "cohere": "Cohere",
    "bytedance": "ByteDance",
}

# Map model name prefixes to organizations
MODEL_ORG_MAP = {
    "claude": "Anthropic",
    "gemini": "Google",
    "grok": "xAI",
    "gpt": "OpenAI",
    "o1": "OpenAI",
    "o3": "OpenAI",
    "o4": "OpenAI",
    "llama": "Meta",
    "deepseek": "DeepSeek",
    "mistral": "Mistral",
    "phi": "Microsoft",
    "command": "Cohere",
    "doubao": "ByteDance",
    "dola": "ByteDance",
    "seed": "ByteDance",
}


def _strip_org_prefix(raw_name: str) -> tuple[str, str | None]:
    """Strip organization name prefix from raw scraped model name.

    Returns (cleaned_name, detected_org_or_none).
    E.g. 'Anthropicclaude-opus-4-6-thinking' -> ('claude-opus-4-6-thinking', 'Anthropic')
    """
    name_lower = raw_name.lower().strip()
    for prefix, org in sorted(ORG_PREFIXES.items(), key=lambda x: -len(x[0])):
        if name_lower.startswith(prefix):
            rest = raw_name[len(prefix):].strip()
            if rest:
                return rest, org
    return raw_name, None


def _infer_org(model_name: str) -> str:
    """Infer organization from model name prefix."""
    name_lower = model_name.lower().strip()
    for prefix, org in MODEL_ORG_MAP.items():
        if name_lower.startswith(prefix):
            return org
    return "Unknown"


def _clean_model_name(raw_name: str) -> str:
    """Convert raw model slug to a clean display name.

    E.g. 'claude-opus-4-6-thinking' -> 'Claude Opus 4.6 (Thinking)'
         'gpt-5.1-high' -> 'GPT-5.1 High'
    """
    # Replace hyphens with spaces
    name = raw_name.replace("-", " ").strip()

    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name)

    # Capitalize words, but handle special cases
    words = name.split()
    cleaned = []
    i = 0
    while i < len(words):
        word = words[i]
        wl = word.lower()

        # Known brand capitalizations
        if wl in ("gpt", "gpt4", "gpt5"):
            cleaned.append(word.upper())
        elif wl == "claude":
            cleaned.append("Claude")
        elif wl == "gemini":
            cleaned.append("Gemini")
        elif wl == "grok":
            cleaned.append("Grok")
        elif wl == "llama":
            cleaned.append("Llama")
        elif wl == "deepseek":
            cleaned.append("DeepSeek")
        elif wl in ("doubao", "dola"):
            cleaned.append("Doubao")
        # Version-like numbers: try to merge adjacent number segments
        # e.g. "4" "6" -> "4.6", "4" "5" -> "4.5"
        elif word.replace(".", "").isdigit():
            # Look ahead: if next word is also a simple number, join with dot
            if (i + 1 < len(words)
                    and words[i + 1].replace(".", "").isdigit()
                    and "." not in word
                    and "." not in words[i + 1]):
                cleaned.append(f"{word}.{words[i + 1]}")
                i += 2
                continue
            else:
                cleaned.append(word)
        # Parenthesize mode qualifiers
        elif wl == "thinking":
            # Check if there's a qualifier after (e.g. "thinking minimal" -> "(Thinking Minimal)")
            if i + 1 < len(words) and words[i + 1].lower() in ("min", "minimal", "max"):
                cleaned.append(f"(Thinking {words[i + 1].capitalize()})")
                i += 2
                continue
            else:
                cleaned.append("(Thinking)")
        elif wl in ("(thinking", ):
            # Handle pre-parenthesized like "(thinking-min..."
            if i + 1 < len(words):
                rest = words[i + 1].rstrip(")")
                cleaned.append(f"(Thinking {rest.capitalize()})")
                i += 2
                continue
            else:
                cleaned.append("(Thinking)")
        elif wl == "high":
            cleaned.append("High")
        elif wl in ("32k", "64k", "128k"):
            cleaned.append(word.upper())
        else:
            cleaned.append(word.capitalize())
        i += 1

    result = " ".join(cleaned)

    # Clean up parenthesization: remove date stamps like 20251101
    result = re.sub(r"\b\d{8}\b\s*", "", result).strip()

    # Clean up double spaces
    result = re.sub(r"\s+", " ", result)

    return result


class ArenaClient:
    LEADERBOARD_URL = "https://arena.ai/leaderboard"

    def __init__(self, cache_ttl_minutes: int = 60):
        self._client = httpx.AsyncClient(timeout=30)
        self._cache: tuple[list[dict], datetime] | None = None
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)

    async def get_rankings(self, top_n: int = 20) -> list[dict]:
        """Fetch top LLM arena rankings. Falls back to static data on failure."""
        if self._cache:
            data, ts = self._cache
            if datetime.now(timezone.utc) - ts < self._cache_ttl:
                return data[:top_n]

        try:
            rankings = await self._try_scrape_arena(top_n)
            if rankings:
                # Backfill orgs from static data that are missing from the live scrape
                # (e.g. Meta/Llama, DeepSeek) so they appear in the spend legend
                scraped_orgs = {r["organization"] for r in rankings}
                next_rank = max(r["rank"] for r in rankings) + 1
                for static in STATIC_RANKINGS:
                    if static["organization"] not in scraped_orgs:
                        rankings.append({**static, "rank": next_rank})
                        scraped_orgs.add(static["organization"])
                        next_rank += 1
                        logger.info(f"Backfilled {static['organization']} ({static['model_name']}) at rank {next_rank - 1}")
                self._cache = (rankings, datetime.now(timezone.utc))
                return rankings[:top_n]
        except Exception as e:
            logger.warning(f"Arena scrape failed: {e}")

        logger.info("Using static LLM arena rankings as fallback")
        return STATIC_RANKINGS[:top_n]

    async def _try_scrape_arena(self, top_n: int) -> list[dict] | None:
        """Try to scrape the arena.ai leaderboard page (Text arena only)."""
        try:
            resp = await self._client.get(
                self.LEADERBOARD_URL,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SaaSpocalypse/1.0)"},
            )
            if resp.status_code != 200:
                logger.warning(f"Arena returned {resp.status_code}")
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # Find the first table only (Text arena) — skip Code, Vision, etc.
            tables = soup.find_all("table")
            if not tables:
                logger.warning("No tables found on arena.ai")
                return None

            first_table = tables[0]
            rankings = []
            rows = first_table.find_all("tr")

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue

                texts = [c.get_text(strip=True) for c in cells]
                try:
                    rank = int(texts[0])
                    raw_model = texts[1]
                    score = int(texts[2].replace(",", ""))
                except (ValueError, IndexError):
                    continue

                # Strip any org prefix from the model name
                model_name, detected_org = _strip_org_prefix(raw_model)

                # Infer org from cleaned model name, or use detected org
                org = detected_org or _infer_org(model_name)

                # Build clean display name
                display_name = _clean_model_name(model_name)

                rankings.append({
                    "rank": rank,
                    "model_name": display_name,
                    "elo_score": score,
                    "organization": org,
                })

                if len(rankings) >= max(top_n, 25):
                    break

            if rankings:
                logger.info(f"Scraped {len(rankings)} models from arena.ai (Text arena)")
                return rankings

            logger.warning("Could not parse arena.ai leaderboard table")
            return None

        except Exception as e:
            logger.warning(f"Arena scrape error: {e}")
            return None

    async def close(self):
        await self._client.aclose()
