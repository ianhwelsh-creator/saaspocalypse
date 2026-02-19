"""AI Proof Evaluator API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import json

from app.database import get_db
from app.models.db_models import Evaluation
from app.models.schemas import EvaluationRequest, EvaluationResponse
from app.routers._deps import get_claude_client
from app.services.evaluator_service import EvaluatorService

router = APIRouter(prefix="/api/evaluator", tags=["evaluator"])


@router.post("/analyze", response_model=EvaluationResponse)
async def analyze_company(req: EvaluationRequest, db: AsyncSession = Depends(get_db)):
    """Run AI analysis on a company for SaaS vulnerability."""
    client = get_claude_client()
    if not client:
        raise HTTPException(status_code=503, detail="Claude API not configured")

    service = EvaluatorService(client)
    return await service.analyze_company(req.company_name, db)


@router.get("/history")
async def get_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Get past evaluations."""
    client = get_claude_client()
    if not client:
        return []
    service = EvaluatorService(client)
    return await service.get_history(db, limit=limit)


@router.get("/reference-companies")
async def get_reference_companies():
    """Get reference companies for the 2x2 matrix."""
    service = EvaluatorService.__new__(EvaluatorService)
    return service.get_reference_companies()


@router.get("/{eval_id}", response_model=EvaluationResponse)
async def get_evaluation(eval_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single evaluation by ID."""
    evaluation = await db.get(Evaluation, eval_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    score_factors = None
    if evaluation.score_factors:
        try:
            score_factors = json.loads(evaluation.score_factors)
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": evaluation.id,
        "company_name": evaluation.company_name,
        "zone": evaluation.zone,
        "overview": evaluation.overview,
        "justification": evaluation.justification,
        "diligence": json.loads(evaluation.diligence),
        "x_score": evaluation.x_score,
        "y_score": evaluation.y_score,
        "score_factors": score_factors,
        "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
    }
