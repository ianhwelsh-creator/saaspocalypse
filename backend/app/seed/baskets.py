"""Stock ticker to zone mapping for SaaS vulnerability baskets."""

BASELINE_DATE = "2026-01-30"

BASKETS = {
    "dead_zone": {
        "label": "Dead Zone",
        "color": "#ef4444",  # red-500
        "description": "Simple workflows, shallow data moat. Existential AI risk.",
        "tickers": ["FRSH", "ZS", "ASAN", "MDB", "FIVN"],
    },
    "compression_zone": {
        "label": "Compression Zone",
        "color": "#f59e0b",  # amber-500
        "description": "Simple workflows, deep data moat. Revenue compression from AI.",
        "tickers": ["HUBS", "BILL", "ZI", "SEMR", "BRZE"],
    },
    "adaptation_zone": {
        "label": "Adaptation Zone",
        "color": "#3b82f6",  # blue-500
        "description": "Complex workflows, shallow data. Must embed AI faster than competition.",
        "tickers": ["ADBE", "TEAM", "DOCN", "TWLO", "DDOG"],
    },
    "fortress_zone": {
        "label": "Fortress Zone",
        "color": "#10b981",  # emerald-500
        "description": "Complex workflows, deep data moat. AI strengthens their position.",
        "tickers": ["VEEV", "NOW", "CRWD", "SNOW", "PCOR", "GWRE"],
    },
    "ai_etfs": {
        "label": "AI ETFs",
        "color": "#a855f7",  # purple-500
        "description": "AI-exposure equity ETFs for comparison.",
        "tickers": ["BOTZ", "AIQ", "ROBT"],
    },
    "sp500": {
        "label": "S&P 500",
        "color": "#6b7280",  # gray-500
        "description": "S&P 500 index benchmark.",
        "tickers": ["SPY"],
    },
}

ALL_TICKERS = []
for basket in BASKETS.values():
    ALL_TICKERS.extend(basket["tickers"])

# Per-ticker rationale bullets for hover tooltips
TICKER_RATIONALE: dict[str, list[str]] = {
    # ── Dead Zone ────────────────────────────────────────────────
    "FRSH": [
        "Simple helpdesk/CRM workflows easily replicated by AI agents",
        "Data is easily exportable via standard APIs",
        "AI chatbots directly replacing core product functionality",
    ],
    "ZS": [
        "Cloud security with increasingly commoditized feature set",
        "Limited proprietary data advantage vs AI-native alternatives",
        "Simple policy-based workflows automatable by AI",
    ],
    "ASAN": [
        "Task management is a simple, templated workflow",
        "AI agents can manage projects end-to-end",
        "No significant data moat — tasks are easily portable",
    ],
    "MDB": [
        "Developer-facing database with low workflow complexity",
        "Data layer is easily swappable (Postgres, serverless alternatives)",
        "AI code assistants reduce need for managed DB tooling",
    ],
    "FIVN": [
        "Cloud contact centre with simple call-routing workflows",
        "AI voice agents directly replace core IVR/ACD functionality",
        "Customer interaction data not deeply proprietary",
    ],
    # ── Compression Zone ─────────────────────────────────────────
    "HUBS": [
        "Rich CRM data creates meaningful customer lock-in",
        "But simple marketing automation workflows are AI-replicable",
        "Revenue per seat will compress as AI handles more tasks",
    ],
    "BILL": [
        "Deep accounts payable/receivable data embedded in workflows",
        "Simple invoice processing increasingly automated by AI",
        "Network effects provide some moat but per-seat value compresses",
    ],
    "ZI": [
        "Massive B2B contact and intent data asset",
        "But sales prospecting workflows are simple and AI-replaceable",
        "Data moat eroding as AI scrapes and enriches contacts directly",
    ],
    "SEMR": [
        "Large SEO/SEM keyword and competitive data set",
        "Marketing analytics workflows are straightforward",
        "AI search evolution may reduce value of traditional SEO data",
    ],
    "BRZE": [
        "Deep customer engagement and behavioural data",
        "Campaign workflows are templated and AI-automatable",
        "Per-message pricing compresses as AI generates content",
    ],
    # ── Adaptation Zone ──────────────────────────────────────────
    "ADBE": [
        "Complex creative workflows spanning multiple tools",
        "Creative assets are not a deep proprietary data moat",
        "Must embed AI faster than Figma, Canva, and new entrants",
    ],
    "TEAM": [
        "Complex developer and IT workflows (Jira, Confluence)",
        "Data is portable — not deeply proprietary",
        "Must rapidly embed AI or risk disruption by Cursor/Copilot etc.",
    ],
    "DOCN": [
        "Developer cloud with moderate workflow complexity",
        "Shallow data moat — workloads easily portable across clouds",
        "Must add AI features to compete with hyperscaler offerings",
    ],
    "TWLO": [
        "Complex communications APIs across channels",
        "Customer comms data is shallow — messages are transient",
        "AI-native messaging platforms emerging as alternatives",
    ],
    "DDOG": [
        "Complex observability across infrastructure and apps",
        "Telemetry data has some gravity but is reproducible",
        "Must embed AI-driven root-cause analysis to stay ahead",
    ],
    # ── Fortress Zone ────────────────────────────────────────────
    "VEEV": [
        "Deeply regulated life sciences workflows (FDA compliance)",
        "Proprietary clinical trial and regulatory data",
        "AI makes their orchestration layer more valuable",
    ],
    "NOW": [
        "Complex enterprise ITSM workflows across departments",
        "Deep institutional process data that can't be replicated",
        "AI enhances their workflow orchestration platform",
    ],
    "CRWD": [
        "Complex threat detection across millions of endpoints",
        "Massive proprietary telemetry data from global sensor network",
        "AI is already core to their value prop — makes them stronger",
    ],
    "SNOW": [
        "Complex data engineering and analytics workflows",
        "Deep data warehouse with customer data gravity",
        "AI/ML workloads make their platform more essential",
    ],
    "PCOR": [
        "Complex construction project management workflows",
        "Deep historical project, compliance, and cost data",
        "Highly regulated industry with institutional lock-in",
    ],
    "GWRE": [
        "Complex insurance underwriting and claims workflows",
        "Proprietary actuarial and policy data spanning decades",
        "Regulated industry where AI enhances core platform",
    ],
    # ── Benchmarks ───────────────────────────────────────────────
    "BOTZ": [
        "Global X Robotics & AI ETF",
        "Tracks companies in robotics, automation, and AI hardware",
        "Benchmark for AI infrastructure investment thesis",
    ],
    "AIQ": [
        "Global X Artificial Intelligence & Technology ETF",
        "Tracks companies developing and leveraging AI software",
        "Benchmark for AI adoption beneficiaries",
    ],
    "ROBT": [
        "First Trust Nasdaq AI & Robotics ETF",
        "Broad AI/robotics/automation exposure",
        "Benchmark for AI ecosystem performance",
    ],
    "SPY": [
        "SPDR S&P 500 ETF Trust",
        "Tracks the S&P 500 broad market index",
        "Baseline comparison for overall market performance",
    ],
}
