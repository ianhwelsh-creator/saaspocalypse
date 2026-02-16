"""AI investment spend by company (in billions USD).

Updated: Feb 2026

Hyperscaler figures = 2026 guided/annualized AI capex.
Startup figures = total raised to date (equity).

Sources:
  - Amazon $200B: CNBC, Feb 2026 (CEO Jassy confirmed, predominantly AWS/AI)
  - Alphabet $180B: guided $175-185B for 2026 (Fortune, Feb 2026)
  - Microsoft $145B: annualized from $37.5B Q2 FY26 spend (Sherwood News)
  - Meta $125B: guided $115-135B for 2026 (Data Center Dynamics, Jan 2026)
  - OpenAI $60B: total raised to date incl. $40B SoftBank Series F (TechCrunch)
  - Anthropic $37B: ~$37.3B raised across 16 rounds, $20B round closing (TechCrunch, Feb 2026)
  - xAI $22B: $22B equity + $5B debt, acquired by SpaceX at $250B (CNBC, Jan 2026)
"""

AI_SPEND = {
    "Google": {"spend_billions": 180, "label": "Alphabet/Google"},
    "Alphabet": {"spend_billions": 180, "label": "Alphabet/Google"},
    "Microsoft": {"spend_billions": 145, "label": "Microsoft"},
    "Meta": {"spend_billions": 125, "label": "Meta"},
    "Amazon": {"spend_billions": 200, "label": "Amazon/AWS"},
    "OpenAI": {"spend_billions": 60, "label": "OpenAI (raised)"},
    "Anthropic": {"spend_billions": 37, "label": "Anthropic (raised)"},
    "xAI": {"spend_billions": 22, "label": "xAI (raised)"},
    "Apple": {"spend_billions": 30, "label": "Apple"},
    "Oracle": {"spend_billions": 16, "label": "Oracle"},
}

# Map model organization names to AI_SPEND keys
ORG_TO_COMPANY = {
    "google": "Google",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "meta": "Meta",
    "microsoft": "Microsoft",
    "amazon": "Amazon",
    "xai": "xAI",
    "mistral": None,
    "cohere": None,
    "deepseek": None,
}
