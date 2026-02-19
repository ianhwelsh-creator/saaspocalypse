"""AI Proof Evaluator service — orchestrates Claude analysis and caches results."""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.claude_client import ClaudeClient
from app.models.db_models import Evaluation
from app.seed.zone_companies import REFERENCE_COMPANIES

logger = logging.getLogger(__name__)


class EvaluatorService:
    def __init__(self, claude_client: ClaudeClient):
        self._claude = claude_client

    async def analyze_company(self, company_name: str, db: AsyncSession) -> dict:
        """Analyze a company and cache the result."""
        result = await self._claude.analyze_company(company_name)

        # Build score_factors JSON from Claude's response
        score_factors = None
        x_factors = result.get("x_factors")
        y_factors = result.get("y_factors")
        if x_factors or y_factors:
            score_factors = json.dumps({
                "x_factors": x_factors or {},
                "y_factors": y_factors or {},
            })

        # Save to DB
        evaluation = Evaluation(
            company_name=result.get("company_name", company_name),
            zone=result.get("zone", "unknown"),
            overview=result.get("overview", ""),
            justification=result.get("justification", ""),
            diligence=json.dumps(result.get("diligence", [])),
            x_score=result.get("x_score", 50),
            y_score=result.get("y_score", 50),
            score_factors=score_factors,
        )
        db.add(evaluation)
        await db.commit()
        await db.refresh(evaluation)

        return self._evaluation_to_dict(evaluation)

    async def get_history(self, db: AsyncSession, limit: int = 20) -> list[dict]:
        """Get past evaluations."""
        stmt = select(Evaluation).order_by(Evaluation.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        evaluations = result.scalars().all()

        return [self._evaluation_to_dict(e) for e in evaluations]

    def get_reference_companies(self) -> list[dict]:
        """Return reference companies for the 2x2 matrix."""
        return REFERENCE_COMPANIES

    @staticmethod
    def _evaluation_to_dict(e: Evaluation) -> dict:
        """Convert an Evaluation ORM instance to a serializable dict."""
        d = {
            "id": e.id,
            "company_name": e.company_name,
            "zone": e.zone,
            "overview": e.overview,
            "justification": e.justification,
            "diligence": json.loads(e.diligence),
            "x_score": e.x_score,
            "y_score": e.y_score,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        if e.score_factors:
            try:
                d["score_factors"] = json.loads(e.score_factors)
            except (json.JSONDecodeError, TypeError):
                d["score_factors"] = None
        else:
            d["score_factors"] = None
        return d
