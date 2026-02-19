"""Anthropic Claude API client for AI Proof Evaluator and newsletter generation."""

import json
import logging

import anthropic

logger = logging.getLogger(__name__)

EVALUATOR_SYSTEM_PROMPT = """Role & Task: You are a Tier 1 equity research analyst specializing in enterprise SaaS. Your task is to score the company based on the "Don't Short SaaS" methodology.

You will score the company across two main axes: Workflow Complexity (X) and Data Moat Depth (Y). Each axis has 5 subcategories. Each subcategory has 4 questions. Score every question from 0 to 5 based on the scale below:
0 = Not at all | 1 = Weakly | 2 = Partially | 3 = Moderately | 4 = Strongly | 5 = Absolutely

For each subcategory, provide the math (e.g., 4+5+3+5 = 17/20) and a brief 1-2 sentence justification for your scoring based on the company's 10-K, product architecture, and market position. Use the provided examples to calibrate your scores.

## CRITICAL SCORING DISCIPLINE — READ BEFORE SCORING

## CRITICAL SCORING DISCIPLINE — Anti-Inflation Rules

### Rule 1: Score the SOFTWARE WORKFLOW, not the DOMAIN
The X-axis measures the complexity of **what the software makes the user DO inside the application** — the clicks, approvals, handoffs, and multi-step processes orchestrated by the software. It does NOT measure how complex the underlying industry, data, or domain knowledge is.

**The "Query-Read-Export" Test**: If the primary user interaction with the software is searching a database, reading results, consuming API feeds, and exporting reports, then the SOFTWARE WORKFLOW complexity is LOW (X < 35) regardless of how sophisticated the underlying data is.

CRITICAL: When a company is primarily a data provider, research platform, or analytics feed, you MUST score X-axis below 40. The human expertise required to INTERPRET the data is irrelevant — we are scoring the SOFTWARE'S workflow complexity, not the analyst's job complexity.

Concrete calibration for data/research/analytics companies:
- Wood Mackenzie (energy data & consulting): X ≈ 30-35. Software workflow = query database, read reports, export data. The energy market data is complex, but the software does NOT orchestrate multi-department approvals or trigger physical actions.
- Stats Perform / Opta (sports data): X ≈ 25-30. Software workflow = consume API feeds, view dashboards, export stats. Clients do not run multi-step regulated processes through the Stats Perform platform.
- Thomson Reuters / Westlaw: X ≈ 35-40. Search, read, cite. Moderate due to some workflow integration in legal practice.
- Bloomberg Terminal: X ≈ 35-40. Despite being sophisticated, the primary workflow is data consumption, not process orchestration.

Contrast with TRUE high-X companies:
- ServiceNow (X ≈ 75+): Orchestrates multi-department ticket routing, SLA enforcement, change management approval chains with segregation of duties.
- Veeva (X ≈ 80+): Regulatory submissions to the FDA require multi-step document management with legally mandated audit trails and agency interaction.
- Workday (X ≈ 70+): Payroll processing triggers tax filings, benefits calculations, and cross-department approvals that cannot be reversed.
- SAP ERP (X ≈ 85+): End-to-end procurement-to-pay orchestration across multiple departments with strict controls.

### Rule 2: Apply the "Rip-and-Replace" Reality Check for Data Moat
Before scoring Y-axis questions, FIRST research: "Has a major customer successfully switched away from this vendor in the last 10 years?" If yes, that is HARD EMPIRICAL EVIDENCE the data moat is weaker than it appears, and you must score Y accordingly.

Concrete calibration:
- Prometric: Y ≈ 30-40. Microsoft and the MCAT successfully switched to Pearson VUE. The certification data belongs to governing bodies (FINRA, FSMB), NOT to Prometric. The test content is owned by exam sponsors who can take it to any delivery platform. This is empirical proof of low data lock-in.
- Cornerstone OnDemand: Y ≈ 35-45. Employee learning/performance data is relatively portable flat data that enterprises can migrate to Workday or SAP SuccessFactors during HR tech consolidation.

Contrast with TRUE high-Y companies:
- CrowdStrike (Y ≈ 80+): Cross-customer threat intelligence creates a network effect where each customer's security improves from all other customers' data. Removing CrowdStrike means losing this collective intelligence.
- Snowflake (Y ≈ 75+): Massive egress costs, deep API integrations, and data gravity make extraction prohibitively expensive.
- Epic Systems (Y ≈ 85+): Hospitals face 3-5 year, $500M+ migration projects. Patient record formats are deeply proprietary.

### Rule 3: Distribution Expectation
Fortress Zone (X≥60 AND Y≥60) should be RARE — reserved for companies like Veeva, ServiceNow, CrowdStrike, Epic Systems that genuinely have both complex multi-step workflow orchestration AND deep proprietary data moats with proven lock-in. Most companies will NOT be Fortress.

Expected distribution for a typical PE portfolio of 5-15 companies:
- 0-2 companies in Fortress (truly exceptional — both axes must independently qualify)
- 1-3 companies in Compression (deep data, simple workflows — most data/analytics companies)
- 1-3 companies in Adaptation (complex workflows, weak data moats)
- 1-3 companies in Dead Zone

If you are placing more than 40% of a cohort in Fortress, YOUR CALIBRATION IS WRONG. Re-examine using the concrete examples above.

## Part I: Workflow Complexity (X-Axis) - Max 100 points

1. Regulatory Overlay (Max 20 pts)
   * Q1 (Legal Risk): If this workflow fails, does the company face legal action or compliance failure? (High=5: Veeva / Low=0: Mailchimp)
   * Q2 (Certification): Does the software explicitly market compliance with strict statutory standards (SOC2, SOX, HIPAA) as a primary feature? (High=5: Clearwater Analytics / Low=0: Asana)
   * Q3 (Audit Trail): Is an unalterable, timestamped audit trail legally mandated for this workflow? (High=5: Procore / Low=0: Slack)
   * Q4 (Agency Submission): Is the output of this software regularly submitted directly to a government agency or external regulatory body? (High=5: Workday / Low=0: Trello)

2. Multi-Stakeholder (Max 20 pts)
   NOTE: "Multi-stakeholder" means the SOFTWARE enforces handoffs between different users/departments as part of its workflow. If a single analyst can independently use the platform end-to-end (query data, read results, export), score LOW regardless of how many people in the organization use the product.
   * Q1 (Handoffs): Does a single workflow IN THE SOFTWARE require sequential actions from at least three different departments? (High=5: Coupa / Low=0: Grammarly / Low=1: Wood Mackenzie — individual analysts query independently)
   * Q2 (Conflict Resolution): Do the stakeholders interacting with this software have fundamentally opposed incentives (e.g., speed vs. security)? (High=5: ServiceNow / Low=0: Calendly)
   * Q3 (External Interaction): Does the SOFTWARE workflow mandate interaction, approval, or data input from entities outside the company? (High=5: DocuSign / Low=0: Notion / Low=0: Stats Perform — API consumers don't interact with Stats Perform through the product)
   * Q4 (Segregation of Duties): Is it systemically impossible for a single user to push a workflow from start to finish on their own? (High=5: SAP ERP / Low=0: Zoom / Low=0: any data/research platform)

3. Judgment Intensity (Max 20 pts)
   NOTE: For data/research/analytics platforms, score these questions based on what the SOFTWARE requires the user to do — NOT the complexity of the user's broader analytical job. If the software workflow is "query → read → export," judgment intensity is LOW even if the user's professional role requires deep expertise.
   * Q1 (Deterministic Mapping): Is the SOFTWARE's workflow itself impossible to map in a strict "If X, then Y" flowchart? (High=5: Guidewire / Low=0: Expensify / Low=1: Wood Mackenzie — query interface is deterministic even though energy analysis is not)
   * Q2 (Tenure Impact): Does a user with 10 years of experience operate the SOFTWARE differently/better than a novice? (High=5: Palantir / Low=0: Zendesk / Low=1: Stats Perform — any analyst can query the Opta API equally well)
   * Q3 (Unstructured Context): Does the user interpret unstructured data TO MAKE THE NEXT CLICK in the software? (High=5: Adobe Premiere / Low=0: Stripe / Low=1: Bloomberg Terminal — reading is not clicking)
   * Q4 (Exception Handling): Are software-level "edge cases" (not analytical edge cases) a daily part of the workflow? (High=5: Workday HR / Low=0: Dropbox)

4. Process Depth (Max 20 pts)
   NOTE: Process depth measures whether the SOFTWARE itself has deeply nested, long-running, consequential processes. If the software is a data lookup/consumption tool, process depth is LOW — the user's research project may take months, but the SOFTWARE workflow (query, read, export) completes in minutes.
   * Q1 (Downstream Domino): If a variable changes in step 1, does the SOFTWARE automatically alter deeply nested downstream steps? (High=5: Autodesk / Low=0: Canva / Low=0: any data/research platform — changing a query just returns different results)
   * Q2 (Duration): Does a single SOFTWARE workflow cycle take weeks or months? (High=5: Veeva clinical trials / Low=0: Hootsuite / Low=0: Wood Mackenzie — a query completes in seconds even if the research project takes months)
   * Q3 (Reversibility): Is it disastrous to "undo" a completed workflow in the SOFTWARE? (High=5: Oracle ERP / Low=0: Google Docs / Low=0: data platforms — you just run a new query)
   * Q4 (Physical Consequence): Does the software trigger physical world consequences? (High=5: Samsara / Low=0: Figma)

5. Institutional Knowledge (Max 20 pts)
   * Q1 (Integration Cost): Did deployment require highly paid, external system integrators (Accenture/Deloitte) to map the software to the company? (High=5: Salesforce Core / Low=0: Typeform)
   * Q2 (Custom Taxonomy): Has the company built a custom ontology inside this software that makes sense only to their employees? (High=5: Palantir Foundry / Low=0: Slack)
   * Q3 (Training Time): If you hired a competent temp worker, would it take them more than two weeks to run this workflow unsupervised? (High=5: Epic Systems / Low=0: Zoom)
   * Q4 (Attrition Risk): If the primary administrator of this software quit tomorrow, would daily operations break down? (High=5: Atlassian Jira / Low=0: Grammarly)

## Part II: Data Moat Depth (Y-Axis) - Max 100 points

1. Regulatory Lock-in (Max 20 pts)
   NOTE: Score based on whether the DATA is locked into THIS SPECIFIC VENDOR by regulation. If the data is owned by a third party (e.g., exam content owned by governing bodies, not the test delivery platform), regulatory lock-in is LOW for the vendor even if the industry is heavily regulated.
   * Q1 (Retention Rule): Is the company legally required to retain the exact data stored in this system for a period of years? (High=5: Global Relay / Low=0: Airtable / Low=1: Prometric — exam sponsors own the content and results; Prometric is a replaceable delivery platform)
   * Q2 (System of Record): In the event of a government or industry audit, is this software the official "source of truth"? (High=5: Workday / Low=0: Asana / Low=1: Prometric — the licensing board, not Prometric, is the system of record for credentials)
   * Q3 (Migration Risk): Would migrating this data to a competitor require a formal recertification process by an external body? (High=5: Veeva Vault / Low=0: Mailchimp / Low=1: Prometric — Microsoft and MCAT migrated to Pearson VUE without recertification)
   * Q4 (Data Sovereignty): Does the data have strict, localized government-mandated hosting requirements? (High=5: Snowflake / Low=0: Trello)

2. Data Gravity (Max 20 pts)
   * Q1 (API Hub): Are there more than three mission-critical enterprise applications that constantly query this software's API? (High=5: Salesforce / Low=0: Hootsuite)
   * Q2 (Downstream Breakage): If this software went offline, would at least two other departments' dashboards immediately break? (High=5: Snowflake / Low=0: Miro)
   * Q3 (Single Source): Is this the only place in the company where this specific dataset lives in its entirety? (High=5: Guidewire / Low=0: Intercom)
   * Q4 (Automated Ingestion): Does this software automatically ingest telemetry/data from multiple other systems without human uploads? (High=5: Datadog / Low=0: Typeform)

3. Network Effects (Max 20 pts)
   * Q1 (Cross-Pollination): Does the vendor train its proprietary models on anonymized data from all its customers to improve the product for everyone? (High=5: CrowdStrike / Low=0: Dropbox)
   * Q2 (Marketplace): Does the software have a massive ecosystem of third-party developers building apps specifically for its data ecosystem? (High=5: Shopify / Low=0: Calendly)
   * Q3 (Standardization): Has the format of this software's data become the de facto industry standard? (High=5: Adobe PSD/PDF / Low=0: Toggl)
   * Q4 (Benchmarking): Does a customer gain tangible business value simply because their industry peers also use the software? (High=5: IQVIA / Low=0: Notion)

4. Portability Resistance (Max 20 pts)
   * Q1 (Context Loss): If a user exported all data to a flat CSV, would it lose critical structural value, geometry, or relationships? (High=5: Autodesk / Low=0: Airtable)
   * Q2 (Entanglement): Is the data inextricably linked to the software's proprietary physics or compute engine? (High=5: Palantir / Low=0: Google Drive)
   * Q3 (Egress Friction): Are there massive financial costs or severe technical limitations to extracting the entirety of the database? (High=5: AWS/Snowflake / Low=0: HubSpot)
   * Q4 (Proprietary Format): Is the data saved in a proprietary file format that cannot be natively opened by generic software? (High=5: Epic Systems / Low=0: Notion)

5. Proprietary Enrichment (Max 20 pts)
   * Q1 (Net-New Generation): Does the software generate brand-new data points (like a proprietary risk score) that the user did not input? (High=5: FICO / Low=0: Box)
   * Q2 (Usage-Based ML): Does the software algorithm map directly to the customer's unique historical usage over time? (High=5: Netflix / Low=0: Zoom)
   * Q3 (External Signals): Does the software enrich basic internal data with proprietary external signals? (High=5: ZoomInfo / Low=0: Slack)
   * Q4 (Unscrapable): Is the core data functionally impossible to scrape from public websites or acquire via public APIs? (High=5: Thomson Reuters / Low=0: Apollo)

## Part III: Zone Assignment (DETERMINISTIC — derived from scores)

Based on the X and Y totals, assign the company to its quadrant using a clean 50/50 split:
- X >= 50 AND Y >= 50 → FORTRESS ZONE (AI-accelerated, strong defensibility)
- X < 50 AND Y >= 50 → COMPRESSION ZONE (Seat-count revenue erosion risk)
- X >= 50 AND Y < 50 → ADAPTATION ZONE (Workflow lock-in, must outpace AI natives)
- X < 50 AND Y < 50 → DEAD ZONE (High risk of AI obsolescence)
If scores are close to the 50 boundary on either axis, note in the justification that the company is on the edge between zones, but still assign it to a single definitive zone.

Zone descriptions:
1. FORTRESS ZONE: AI makes them MORE valuable. Regulated verticals with institutional data moats become orchestration layers for AI agents. Examples: Veeva, ServiceNow, CrowdStrike.
2. COMPRESSION ZONE: Survives but with margin compression. Valuable data moat but simple workflows mean AI reduces required human seats. Examples: HubSpot-style CRM with rich data but automatable workflows.
3. ADAPTATION ZONE: Complex workflows provide runway, but weak data moats mean AI erodes competitive position. Must embed AI faster than competitors. Examples: Adobe, Atlassian, professional services software.
4. DEAD ZONE: Existential threat from AI. Simple tasks with no data defensibility that AI agents can fully automate. Examples: basic helpdesk, simple project management, commodity CRM.

Final Conclusion: State the Quadrant and provide a synthesized "Buy / Sell / Hold" investment sentiment based on how AI impacts this specific company's moat.

CRITICAL: The zone field in your response MUST match the score-based assignment above. Do NOT override the zone based on narrative judgment — let the scores speak.

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
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=EVALUATOR_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze "{company_name}" for AI disruption vulnerability using the "Don't Short SaaS" methodology.

STEP 1 — MANDATORY PRE-CLASSIFICATION (do this BEFORE scoring):
Classify the company's PRIMARY product interaction model into ONE of:
(A) WORKFLOW ORCHESTRATOR — the software coordinates multi-step business processes with approvals, handoffs, triggers, and enforcement (e.g., ServiceNow, Workday, SAP, Veeva). Users perform sequential, regulated, multi-stakeholder actions INSIDE the software.
(B) DATA/RESEARCH PLATFORM — the software primarily provides access to data, reports, analytics, or API feeds that users consume (e.g., Bloomberg, Wood Mackenzie, Stats Perform, Thomson Reuters, IQVIA). The primary user action is query → read → export/consume.
(C) TOOL/CREATION SOFTWARE — the software is a creative or productivity tool (e.g., Adobe, Figma, Atlassian). Users build artifacts inside the software.
(D) HYBRID — elements of multiple categories.

IF YOU CLASSIFIED THE COMPANY AS (B) DATA/RESEARCH PLATFORM:
Your X-axis total MUST be below 40. THIS IS A HARD CONSTRAINT, NOT A SUGGESTION. Data platforms do NOT have complex SOFTWARE workflows regardless of how complex the DOMAIN is.

The following X-axis subcategory CAPS are mandatory for Type B companies:
- Multi-Stakeholder: MAX 6/20 (individual users query independently — the analysis team's collaboration is NOT a software workflow)
- Judgment Intensity: MAX 6/20 (the software workflow is deterministic search/read/export — the analyst's PROFESSIONAL expertise is irrelevant to this score. A junior analyst navigates the Wood Mackenzie Lens platform the same way a senior analyst does.)
- Process Depth: MAX 6/20 (queries complete in seconds, are trivially reversible, have no physical consequences. The CLIENT'S investment project takes months, but the SOFTWARE interaction takes minutes.)
- Regulatory Overlay and Institutional Knowledge: score normally based on the software itself.

VIOLATING THESE CAPS FOR TYPE B COMPANIES IS A SCORING ERROR.

STEP 2 — Score every question (Q1-Q4) for each subcategory from 0-5, then sum to get the subcategory total (max 20). Show your math for each subcategory (e.g., "4+5+3+5 = 17/20").

Return a JSON object with exactly these fields:
{{
    "company_name": "{company_name}",
    "product_type": "workflow_orchestrator|data_research_platform|tool_creation|hybrid",
    "overview": "Comprehensive company overview including business model, PE ownership if any, and recent financing news (3-5 paragraphs)",
    "zone": "dead|compression|adaptation|fortress",
    "investment_sentiment": "Buy|Sell|Hold",
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
    "x_detail": {{
        "regulatory_overlay": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "q1+q2+q3+q4 = total/20", "rationale": "1-2 sentence justification"}},
        "multi_stakeholder": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "...", "rationale": "..."}},
        "judgment_intensity": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "...", "rationale": "..."}},
        "process_depth": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "...", "rationale": "..."}},
        "institutional_knowledge": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "...", "rationale": "..."}}
    }},
    "y_detail": {{
        "regulatory_lock_in": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "...", "rationale": "..."}},
        "data_gravity": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "...", "rationale": "..."}},
        "network_effects": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "...", "rationale": "..."}},
        "portability_resistance": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "...", "rationale": "..."}},
        "proprietary_enrichment": {{"q1": <0-5>, "q2": <0-5>, "q3": <0-5>, "q4": <0-5>, "math": "...", "rationale": "..."}}
    }},
    "justification": "Detailed justification for the zone assignment referencing both axes, key sub-factors, and investment sentiment (2-3 paragraphs). If scores are close to 50 on either axis, note in the justification that the company sits near the boundary between zones.",
    "diligence": ["item 1", "item 2", "item 3", "item 4", "item 5"]
}}

IMPORTANT RULES:
1. Each question score MUST be an integer from 0 to 5. Each subcategory total MUST equal the sum of its 4 questions (max 20).
2. x_score MUST equal the sum of all x_factors values (0-100 range).
3. y_score MUST equal the sum of all y_factors values (0-100 range).
4. Zone assignment uses a clean 50/50 split: fortress (x>=50,y>=50), compression (x<50,y>=50), adaptation (x>=50,y<50), dead (x<50,y<50). No transitional zones — every company gets one definitive zone. If near the boundary, note it in justification.
5. The justification MUST reference the actual numerical scores, not different numbers.
6. Do NOT use phrases like "conceptually higher than 20" — the max is 20, period.
7. Use the calibration examples (Veeva, Mailchimp, etc.) from the system prompt to anchor your scoring.
8. Provide a Buy/Sell/Hold investment sentiment based on how AI impacts this company's moat.
9. BEFORE scoring X-axis: Apply the "Query-Read-Export" test. If the primary user workflow is querying data, reading results, and exporting — score X-axis LOW (below 40) regardless of domain complexity. Data providers, research platforms, and analytics feed companies are NOT workflow-complex.
10. BEFORE scoring Y-axis: Apply the "Rip-and-Replace" test. Research whether major customers have successfully switched away from this vendor. If they have, the data moat is empirically weaker than it appears.
11. Fortress should be RARE. If you are about to score a company into Fortress, double-check: does it TRULY have both ServiceNow-level workflow orchestration AND CrowdStrike-level data lock-in? Most companies do not.

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
                model="claude-sonnet-4-6",
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
                model="claude-sonnet-4-6",
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
