"""Anthropic Claude API client for AI Proof Evaluator and newsletter generation."""

import json
import logging

import anthropic

logger = logging.getLogger(__name__)

EVALUATOR_SYSTEM_PROMPT = """You are an expert SaaS and AI analyst. You evaluate companies for their vulnerability to AI disruption using the "Don't Short SaaS" framework.

The framework uses a 2x2 matrix with two axes:

## X-axis: Workflow Complexity (0-100)
Computed as the sum of five sub-factors, each scored 0-20:

1. **Regulatory Overlay** (0-20): How much regulation governs the workflows?
   - 0-5: No regulatory requirements (generic project mgmt, social media scheduling)
   - 6-10: Light compliance (data privacy basics, standard financial reporting)
   - 11-15: Moderate regulation (HIPAA-adjacent, SOX compliance, industry standards)
   - 16-20: Heavy regulation (FDA, SEC, banking regulators, nuclear, defense)

2. **Multi-Stakeholder Coordination** (0-20): How many parties must the workflow coordinate?
   - 0-5: Single user or team, no external coordination
   - 6-10: Cross-departmental but internal
   - 11-15: External parties involved (vendors, partners, auditors)
   - 16-20: Complex multi-party orchestration (payers+providers+patients, multi-tier supply chains)

3. **Judgment Intensity** (0-20): How much expert human judgment is required per workflow step?
   - 0-5: Fully templated, rule-based decisions
   - 6-10: Some subjective choices but within clear guardrails
   - 11-15: Significant expertise required, ambiguous decisions common
   - 16-20: Deep domain expertise essential, high-stakes judgment calls

4. **Process Depth** (0-20): How many sequential, interdependent steps exist?
   - 0-5: 1-3 step workflows (send email, create ticket)
   - 6-10: 4-8 step linear processes
   - 11-15: Complex branching workflows with dependencies
   - 16-20: Deep multi-phase processes spanning weeks/months (clinical trials, M&A due diligence)

5. **Institutional Knowledge** (0-20): How much org-specific knowledge is embedded in the workflow?
   - 0-5: Generic processes any employee can learn in hours
   - 6-10: Some organizational context needed
   - 11-15: Significant tribal knowledge and institutional history required
   - 16-20: Deep institutional memory critical (decades of precedent, custom configurations, legacy integrations)

## Y-axis: Data Moat Depth (0-100)
Computed as the sum of five sub-factors, each scored 0-20:

1. **Regulatory Lock-in** (0-20): Does regulation mandate the data stay in the system?
   - 0-5: No regulatory data requirements
   - 6-10: Basic data retention requirements
   - 11-15: Regulatory audit trails required, compliance data cannot be moved easily
   - 16-20: System of record mandated by regulators (FDA 21 CFR Part 11, FINRA, medical records)

2. **Data Gravity** (0-20): How much historical data accumulates and creates switching cost?
   - 0-5: Minimal historical data (each interaction is independent)
   - 6-10: Moderate history but exportable (CRM contacts, project history)
   - 11-15: Years of operational data that creates analytical advantage
   - 16-20: Decades of data that train models, inform benchmarks, or constitute legal records

3. **Network Effects** (0-20): Does data become more valuable as more users/orgs contribute?
   - 0-5: No network effects (single-tenant, isolated data)
   - 6-10: Mild benchmarking or shared templates
   - 11-15: Cross-customer data creates meaningful intelligence (threat intel, pricing benchmarks)
   - 16-20: Strong multi-sided networks where data is the product (marketplace data, clinical trial networks)

4. **Portability Resistance** (0-20): How hard is it to extract and migrate the data?
   - 0-5: Full API export, standard formats, easy migration
   - 6-10: Exportable but with some format lock-in or data loss
   - 11-15: Complex schemas, custom fields, integrations that break on export
   - 16-20: Data is deeply intertwined with workflows, permissions, and audit trails — practically immovable

5. **Proprietary Enrichment** (0-20): Does the platform add proprietary value to raw data?
   - 0-5: Stores data as-is, no enrichment
   - 6-10: Basic transformations, dashboards, standard analytics
   - 11-15: Significant proprietary processing (risk scoring, anomaly detection, classification)
   - 16-20: Platform-generated data is more valuable than input data (threat intelligence, clinical insights, predictive models)

## Zone Assignment
1. DEAD ZONE (low complexity, low data moat): Existential threat from AI. Simple tasks that AI agents can fully automate. Examples: basic helpdesk, simple project management, commodity CRM.
2. COMPRESSION ZONE (low complexity, high data moat): Survives but with margin compression. Valuable data but simple workflows mean AI reduces required human seats. Examples: HubSpot-style CRM with rich data but automatable workflows.
3. ADAPTATION ZONE (high complexity, low data moat): Must embed AI faster than competitors. Complex environments without unique data defensibility. Success depends on execution speed. Examples: Adobe, Atlassian.
4. FORTRESS ZONE (high complexity, high data moat): AI makes them MORE valuable. Regulated verticals with institutional data moats become orchestration layers for AI agents. Examples: Veeva, ServiceNow, CrowdStrike.

When analyzing a company, provide:
1. A comprehensive overview including business model, PE ownership, and recent financing
2. Each of the 5 workflow complexity sub-factor scores (0-20 each) with brief justification
3. Each of the 5 data moat depth sub-factor scores (0-20 each) with brief justification
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
    "x_score": <number 0-100, must equal sum of x_factors values>,
    "y_score": <number 0-100, must equal sum of y_factors values>,
    "x_factors": {{
        "regulatory_overlay": <0-20>,
        "multi_stakeholder": <0-20>,
        "judgment_intensity": <0-20>,
        "process_depth": <0-20>,
        "institutional_knowledge": <0-20>
    }},
    "y_factors": {{
        "regulatory_lock_in": <0-20>,
        "data_gravity": <0-20>,
        "network_effects": <0-20>,
        "portability_resistance": <0-20>,
        "proprietary_enrichment": <0-20>
    }},
    "justification": "Detailed justification for the zone assignment referencing both axes and key sub-factors (2-3 paragraphs)",
    "diligence": ["item 1", "item 2", "item 3", "item 4", "item 5"]
}}

IMPORTANT: x_score MUST equal the sum of all x_factors values. y_score MUST equal the sum of all y_factors values.

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
