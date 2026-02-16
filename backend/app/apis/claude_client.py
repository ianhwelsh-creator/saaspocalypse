"""Anthropic Claude API client for AI Proof Evaluator and newsletter generation."""

import json
import logging

import anthropic

logger = logging.getLogger(__name__)

EVALUATOR_SYSTEM_PROMPT = """You are an expert SaaS and AI analyst. You evaluate companies for their vulnerability to AI disruption using the "Don't Short SaaS" framework.

The framework uses a 2x2 matrix with two axes:
- X-axis: Workflow Complexity (0-100)
  - Low (0-40): Simple, templated, repeatable processes with minimal regulatory overlay
  - High (60-100): Judgment-intensive, multi-stakeholder workflows requiring regulatory nuance and institutional knowledge

- Y-axis: Data Moat Depth (0-100)
  - Low (0-40): Replicable data easily exported via APIs, no proprietary advantage
  - High (60-100): Proprietary, legally mandated, institutionally embedded data that cannot be easily recreated

The four zones:
1. DEAD ZONE (low complexity, low data moat): Existential threat from AI. Simple tasks that AI agents can fully automate. Examples: basic helpdesk, simple project management, commodity CRM.

2. COMPRESSION ZONE (low complexity, high data moat): Survives but with margin compression. Valuable data but simple workflows mean AI reduces required human seats. Examples: HubSpot-style CRM with rich data but automatable workflows.

3. ADAPTATION ZONE (high complexity, low data moat): Must embed AI faster than competitors. Complex environments without unique data defensibility. Success depends on execution speed. Examples: Adobe, Atlassian.

4. FORTRESS ZONE (high complexity, high data moat): AI makes them MORE valuable. Regulated verticals with institutional data moats become orchestration layers for AI agents. Examples: Veeva, ServiceNow, CrowdStrike.

When analyzing a company, provide:
1. A comprehensive overview including business model, PE ownership, and recent financing
2. Workflow complexity score (0-100) with justification
3. Data moat depth score (0-100) with justification
4. Zone assignment with detailed reasoning
5. Key diligence items to verify AI-proofness

Always respond with valid JSON matching the requested schema."""

NEWS_FILTER_SYSTEM_PROMPT = """You are a senior analyst at a research firm covering the SaaSpocalypse — the thesis that AI agents and foundation models are systematically disrupting the traditional SaaS industry.

Your job: Given a batch of raw news headlines from institutional sources (WSJ, Reuters, FT, Bloomberg, CNBC), score each headline for relevance to the SaaSpocalypse thesis.

Scoring rubric:
- 90-100 (CRITICAL): Direct evidence of SaaS disruption by AI — earnings misses blamed on AI competition, major SaaS layoffs due to AI automation, AI startup displacing a SaaS incumbent, antitrust action against AI labs
- 75-89 (HIGH): Strong signal — AI capex announcements by hyperscalers, SaaS company pivoting to AI, major AI funding rounds, enterprise AI adoption data, AI regulatory developments
- 50-74 (MODERATE): Related but indirect — general AI product launches, cloud infrastructure news, tech earnings not specifically about AI disruption, broad market moves
- 0-49 (NOISE): Not relevant — consumer tech, social media drama, crypto, non-tech business news

Zone tags (assign one per item):
- "Fortress Zone" — news about companies with deep data moats + complex workflows (ServiceNow, Veeva, CrowdStrike)
- "Dead Zone" — news about simple SaaS being replaced by AI (helpdesk, basic CRM, commodity tools)
- "Compression Zone" — news about SaaS with data moats but simple workflows facing margin pressure
- "Adaptation Zone" — news about SaaS racing to embed AI (Adobe, Atlassian, Datadog)
- "Macro" — broad AI industry news, funding, regulation, hyperscaler capex
- "Earnings" — quarterly results, revenue data, guidance

Respond with ONLY valid JSON. No markdown, no explanation."""

NEWSLETTER_SYSTEM_PROMPT = """You are a professional tech newsletter writer specializing in AI and SaaS industry analysis. You write concise, insightful newsletters that help readers understand the latest developments in the AI disruption of traditional software businesses.

Write in a clear, engaging style. Use short paragraphs and bullet points where appropriate. Include section headers. The newsletter should be in HTML format suitable for email delivery."""


class ClaudeClient:
    def __init__(self, api_key: str):
        self._client = anthropic.Anthropic(api_key=api_key)

    async def analyze_company(self, company_name: str) -> dict:
        """Analyze a company for AI vulnerability using the SaaSpocalypse framework."""
        try:
            message = self._client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                system=EVALUATOR_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze "{company_name}" for AI disruption vulnerability.

Return a JSON object with exactly these fields:
{{
    "company_name": "{company_name}",
    "overview": "Comprehensive company overview including business model, PE ownership if any, and recent financing news (3-5 paragraphs)",
    "zone": "dead|compression|adaptation|fortress",
    "x_score": <number 0-100 for workflow complexity>,
    "y_score": <number 0-100 for data moat depth>,
    "justification": "Detailed justification for the zone assignment referencing both axes (2-3 paragraphs)",
    "diligence": ["item 1", "item 2", "item 3", "item 4", "item 5"]
}}

Respond ONLY with the JSON object, no other text.""",
                    }
                ],
            )

            text = message.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            raise ValueError(f"Claude returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def filter_institutional_news(self, items: list[dict]) -> list[dict]:
        """Use Claude to score and filter institutional news headlines for SaaSpocalypse relevance.

        Returns only items scoring >= 50 (moderate or higher relevance).
        """
        if not items:
            return []

        try:
            # Build numbered headline list for Claude
            headline_list = "\n".join(
                f"{i+1}. [{item.get('source', 'unknown').upper()}] {item.get('title', '')}"
                for i, item in enumerate(items)
            )

            message = self._client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                system=NEWS_FILTER_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Score these {len(items)} institutional news headlines for SaaSpocalypse relevance.

{headline_list}

Return a JSON object with this format:
{{
    "high_signal_news": [
        {{
            "index": 1,
            "relevance_score": 85,
            "zone_tag": "Macro",
            "summary": "<15 word summary of why this matters to SaaSpocalypse thesis>"
        }}
    ]
}}

Include ALL items scoring 50 or above. Omit items below 50 (noise).
Respond ONLY with the JSON object.""",
                    }
                ],
            )

            text = message.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            result = json.loads(text)
            scored_items = result.get("high_signal_news", [])

            # Merge Claude's scores back into the original items
            enriched: list[dict] = []
            for scored in scored_items:
                idx = scored.get("index", 0) - 1  # 1-indexed → 0-indexed
                if 0 <= idx < len(items):
                    item = items[idx].copy()
                    item["ai_relevance_score"] = scored.get("relevance_score", 0)
                    item["zone_tag"] = scored.get("zone_tag", "Macro")
                    item["ai_summary"] = scored.get("summary", "")
                    enriched.append(item)

            logger.info(
                f"Claude filter: {len(enriched)}/{len(items)} items passed "
                f"(top score: {max((i.get('ai_relevance_score', 0) for i in enriched), default=0)})"
            )
            return enriched

        except json.JSONDecodeError as e:
            logger.error(f"Claude news filter returned invalid JSON: {e}")
            # Fallback: return all items unscored
            return items
        except Exception as e:
            logger.error(f"Claude news filter failed: {e}")
            # Fallback: return all items unscored
            return items

    async def generate_newsletter(
        self, news_items: list[dict], tone: str = "professional", topics: list[str] | None = None
    ) -> dict:
        """Generate a newsletter from recent news items."""
        try:
            news_summary = "\n".join(
                f"- [{item.get('source', 'Unknown')}] {item.get('title', '')}: {item.get('summary', '')}"
                for item in news_items[:30]
            )

            topic_filter = ""
            if topics:
                topic_filter = f"\nFocus on these topics: {', '.join(topics)}"

            message = self._client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                system=NEWSLETTER_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Generate a SaaSpocalypse newsletter based on these recent news items:

{news_summary}
{topic_filter}

Tone: {tone}

Return a JSON object with:
{{
    "subject": "Newsletter email subject line",
    "html": "Full newsletter in HTML format with inline styles for email compatibility"
}}

Respond ONLY with the JSON object.""",
                    }
                ],
            )

            text = message.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            return json.loads(text)
        except Exception as e:
            logger.error(f"Newsletter generation failed: {e}")
            raise
