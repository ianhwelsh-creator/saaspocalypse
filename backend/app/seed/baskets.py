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
}

ALL_TICKERS = []
for basket in BASKETS.values():
    ALL_TICKERS.extend(basket["tickers"])
