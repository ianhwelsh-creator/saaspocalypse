"""Reference companies for the 2x2 vulnerability matrix with pre-set positions."""


def _logo(domain: str) -> str:
    """Google Favicon API — reliable, no auth, 128px PNG."""
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"


REFERENCE_COMPANIES = [
    {
        "name": "Freshworks",
        "ticker": "FRSH",
        "zone": "dead",
        "x": 15,
        "y": 30,
        "bullets": [
            "Simple helpdesk/CRM workflows easily replicated by AI agents",
            "Data is easily exportable via standard APIs",
            "AI chatbots directly replacing core product functionality",
        ],
        "logo_url": _logo("freshworks.com"),
    },
    {
        "name": "Zscaler",
        "ticker": "ZS",
        "zone": "dead",
        "x": 35,
        "y": 14,
        "bullets": [
            "Cloud security with increasingly commoditized feature set",
            "Limited proprietary data advantage vs AI-native alternatives",
            "Simple policy-based workflows automatable by AI",
        ],
        "logo_url": _logo("zscaler.com"),
    },
    {
        "name": "Asana",
        "ticker": "ASAN",
        "zone": "dead",
        "x": 25,
        "y": 42,
        "bullets": [
            "Task management is a simple, templated workflow",
            "AI agents can manage projects end-to-end",
            "No significant data moat - tasks are easily portable",
        ],
        "logo_url": _logo("asana.com"),
    },
    {
        "name": "HubSpot",
        "ticker": "HUBS",
        "zone": "compression",
        "x": 30,
        "y": 70,
        "bullets": [
            "Rich CRM data creates meaningful customer lock-in",
            "But simple marketing automation workflows are AI-replicable",
            "Revenue per seat will compress as AI handles more tasks",
        ],
        "logo_url": _logo("hubspot.com"),
    },
    {
        "name": "Bill Holdings",
        "ticker": "BILL",
        "zone": "compression",
        "x": 25,
        "y": 65,
        "bullets": [
            "Deep accounts payable/receivable data embedded in workflows",
            "Simple invoice processing increasingly automated by AI",
            "Network effects provide some moat but per-seat value compresses",
        ],
        "logo_url": _logo("bill.com"),
    },
    {
        "name": "Adobe",
        "ticker": "ADBE",
        "zone": "adaptation",
        "x": 75,
        "y": 35,
        "bullets": [
            "Complex creative workflows spanning multiple tools",
            "But creative assets are not a deep proprietary data moat",
            "Must embed AI faster than Figma, Canva, and new entrants",
        ],
        "logo_url": _logo("adobe.com"),
    },
    {
        "name": "Atlassian",
        "ticker": "TEAM",
        "zone": "adaptation",
        "x": 70,
        "y": 40,
        "bullets": [
            "Complex developer and IT workflows (Jira, Confluence)",
            "Data is portable - not deeply proprietary",
            "Must rapidly embed AI or risk disruption by Cursor/Copilot etc.",
        ],
        "logo_url": _logo("atlassian.com"),
    },
    {
        "name": "Veeva Systems",
        "ticker": "VEEV",
        "zone": "fortress",
        "x": 92,
        "y": 95,
        "bullets": [
            "Deeply regulated life sciences workflows (FDA compliance)",
            "Proprietary clinical trial and regulatory data",
            "AI makes their orchestration layer more valuable",
        ],
        "logo_url": _logo("veeva.com"),
    },
    {
        "name": "ServiceNow",
        "ticker": "NOW",
        "zone": "fortress",
        "x": 75,
        "y": 90,
        "bullets": [
            "Complex enterprise ITSM workflows across departments",
            "Deep institutional process data that can't be replicated",
            "AI enhances their workflow orchestration platform",
        ],
        "logo_url": _logo("servicenow.com"),
    },
    {
        "name": "CrowdStrike",
        "ticker": "CRWD",
        "zone": "fortress",
        "x": 60,
        "y": 82,
        "bullets": [
            "Complex threat detection across millions of endpoints",
            "Massive proprietary telemetry data from global sensor network",
            "AI is already core to their value prop - makes them stronger",
        ],
        "logo_url": _logo("crowdstrike.com"),
    },
    {
        "name": "Snowflake",
        "ticker": "SNOW",
        "zone": "fortress",
        "x": 68,
        "y": 72,
        "bullets": [
            "Complex data engineering and analytics workflows",
            "Deep data warehouse with customer data gravity",
            "AI/ML workloads make their platform more essential",
        ],
        "logo_url": _logo("snowflake.com"),
    },
    {
        "name": "Procore",
        "ticker": "PCOR",
        "zone": "fortress",
        "x": 85,
        "y": 78,
        "bullets": [
            "Complex construction project management workflows",
            "Deep historical project, compliance, and cost data",
            "Highly regulated industry with institutional lock-in",
        ],
        "logo_url": _logo("procore.com"),
    },
    {
        "name": "Guidewire",
        "ticker": "GWRE",
        "zone": "fortress",
        "x": 80,
        "y": 62,
        "bullets": [
            "Complex insurance underwriting and claims workflows",
            "Proprietary actuarial and policy data spanning decades",
            "Regulated industry where AI enhances core platform",
        ],
        "logo_url": _logo("guidewire.com"),
    },
]
