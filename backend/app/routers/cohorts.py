"""Cohort Evaluator API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import CohortCreateRequest, CohortEditRequest
from app.routers._deps import get_cohort_service
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/cohorts", tags=["cohorts"])


@router.post("")
async def create_cohort(req: CohortCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create a named cohort and start batch analysis."""
    service = get_cohort_service()
    if not service:
        raise HTTPException(status_code=503, detail="Claude API not configured")
    if not req.company_names:
        raise HTTPException(status_code=400, detail="At least one company name required")
    if len(req.company_names) > 25:
        raise HTTPException(status_code=400, detail="Maximum 25 companies per cohort")
    return await service.create_cohort(req.name, req.company_names, db)


@router.get("")
async def list_cohorts(db: AsyncSession = Depends(get_db)):
    """List all cohorts."""
    service = get_cohort_service()
    if not service:
        return []
    return await service.list_cohorts(db)


@router.get("/{cohort_id}")
async def get_cohort(cohort_id: int, db: AsyncSession = Depends(get_db)):
    """Get cohort detail with progress and member evaluations."""
    service = get_cohort_service()
    if not service:
        raise HTTPException(status_code=503, detail="Claude API not configured")
    result = await service.get_cohort_detail(cohort_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return result


@router.get("/{cohort_id}/matrix")
async def get_cohort_matrix(cohort_id: int, db: AsyncSession = Depends(get_db)):
    """Get cohort companies formatted for MatrixChart rendering."""
    service = get_cohort_service()
    if not service:
        raise HTTPException(status_code=503, detail="Claude API not configured")
    return await service.get_cohort_matrix(cohort_id, db)


@router.get("/{cohort_id}/report")
async def get_cohort_report(cohort_id: int, db: AsyncSession = Depends(get_db)):
    """Generate and return a PDF report for the cohort."""
    service = get_cohort_service()
    if not service:
        raise HTTPException(status_code=503, detail="Claude API not configured")

    data = await service.get_cohort_report_data(cohort_id, db)
    if not data:
        raise HTTPException(status_code=404, detail="Cohort not found or not complete")

    report_service = ReportService()
    pdf_bytes = report_service.generate_cohort_report(
        cohort_name=data["cohort_name"],
        cohort_created_at=data["cohort_created_at"],
        members=data["members"],
        evaluations=data["evaluations"],
    )

    safe_name = data["cohort_name"].replace(" ", "_").replace("/", "-")
    filename = f"{safe_name}_report.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put("/{cohort_id}")
async def edit_cohort(cohort_id: int, req: CohortEditRequest, db: AsyncSession = Depends(get_db)):
    """Edit a cohort — add or remove companies."""
    service = get_cohort_service()
    if not service:
        raise HTTPException(status_code=503, detail="Claude API not configured")
    try:
        result = await service.edit_cohort(
            cohort_id, req.add_companies, req.remove_evaluation_ids, db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return result


@router.delete("/{cohort_id}")
async def delete_cohort(cohort_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a cohort and its member links."""
    service = get_cohort_service()
    if not service:
        raise HTTPException(status_code=503, detail="Claude API not configured")
    deleted = await service.delete_cohort(cohort_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return {"ok": True}
