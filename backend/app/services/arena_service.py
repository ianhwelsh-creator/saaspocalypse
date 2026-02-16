"""Arena rankings service — merges rankings with AI spend data."""

import logging

from app.apis.arena_client import ArenaClient
from app.seed.ai_spend import AI_SPEND, ORG_TO_COMPANY

logger = logging.getLogger(__name__)


class ArenaService:
    def __init__(self, client: ArenaClient):
        self._client = client

    async def get_rankings_with_spend(self, top_n: int = 15) -> list[dict]:
        """Get arena rankings enriched with AI investment spend data."""
        rankings = await self._client.get_rankings(top_n)

        enriched = []
        for r in rankings:
            org = r.get("organization", "").lower()
            company_key = ORG_TO_COMPANY.get(org)
            spend = None
            if company_key and company_key in AI_SPEND:
                spend = AI_SPEND[company_key]["spend_billions"]

            enriched.append({
                "rank": r["rank"],
                "model_name": r["model_name"],
                "elo_score": r["elo_score"],
                "organization": r["organization"],
                "ai_spend_billions": spend,
            })

        return enriched
