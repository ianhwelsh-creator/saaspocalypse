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

        # Build score_factors JSON from Claude's response (clamp each sub-factor to 0-20)
        score_factors = None
        x_factors = result.get("x_factors")
        y_factors = result.get("y_factors")
        x_detail = result.get("x_detail")
        y_detail = result.get("y_detail")
        investment_sentiment = result.get("investment_sentiment")
        if x_factors or y_factors:
            clamped_x = {k: max(0, min(20, v)) for k, v in (x_factors or {}).items()}
            clamped_y = {k: max(0, min(20, v)) for k, v in (y_factors or {}).items()}
            factors_data = {
                "x_factors": clamped_x,
                "y_factors": clamped_y,
            }
            if x_detail:
                factors_data["x_detail"] = x_detail
            if y_detail:
                factors_data["y_detail"] = y_detail
            if investment_sentiment:
                factors_data["investment_sentiment"] = investment_sentiment
            score_factors = json.dumps(factors_data)

        # Recalculate scores from clamped factors if available, otherwise clamp raw scores
        if x_factors:
            x_score = sum(max(0, min(20, v)) for v in x_factors.values())
        else:
            x_score = max(0, min(100, result.get("x_score", 50)))
        if y_factors:
            y_score = sum(max(0, min(20, v)) for v in y_factors.values())
        else:
            y_score = max(0, min(100, result.get("y_score", 50)))

        # Derive zone deterministically from scores
        zone = self._derive_zone(x_score, y_score)

        # Save to DB
        evaluation = Evaluation(
            company_name=result.get("company_name", company_name),
            zone=zone,
            overview=result.get("overview", ""),
            justification=result.get("justification", ""),
            diligence=json.dumps(result.get("diligence", [])),
            x_score=x_score,
            y_score=y_score,
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
    def _derive_zone(x_score: int, y_score: int) -> str:
        """Derive zone deterministically from scores using a clean 50/50 split.

        X-axis = Workflow Complexity, Y-axis = Data Moat Depth.
        - Fortress:    x >= 50 AND y >= 50
        - Compression: x < 50 AND y >= 50
        - Adaptation:  x >= 50 AND y < 50
        - Dead Zone:   x < 50 AND y < 50
        """
        if x_score >= 50 and y_score >= 50:
            return "fortress"
        elif x_score < 50 and y_score >= 50:
            return "compression"
        elif x_score >= 50 and y_score < 50:
            return "adaptation"
        else:
            return "dead"

    @staticmethod
    def _evaluation_to_dict(e: Evaluation) -> dict:
        """Convert an Evaluation ORM instance to a serializable dict."""
        # Always derive zone from scores to ensure consistency
        x = int(e.x_score) if e.x_score is not None else 50
        y = int(e.y_score) if e.y_score is not None else 50
        zone = EvaluatorService._derive_zone(x, y)

        d = {
            "id": e.id,
            "company_name": e.company_name,
            "zone": zone,
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
