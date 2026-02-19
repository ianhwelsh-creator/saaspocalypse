"""Cohort Evaluator service — batch analysis with progress tracking."""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.claude_client import ClaudeClient
from app.database import async_session
from app.models.db_models import Cohort, CohortMember, Evaluation

logger = logging.getLogger(__name__)


def derive_zone(x_score, y_score) -> str:
    """Derive zone deterministically from scores using a clean 50/50 split.

    X = Workflow Complexity, Y = Data Moat Depth.
    - Fortress:    x >= 50 AND y >= 50
    - Compression: x < 50 AND y >= 50
    - Adaptation:  x >= 50 AND y < 50
    - Dead Zone:   x < 50 AND y < 50
    """
    x = int(x_score) if x_score is not None else 50
    y = int(y_score) if y_score is not None else 50
    if x >= 50 and y >= 50:
        return "fortress"
    elif x < 50 and y >= 50:
        return "compression"
    elif x >= 50 and y < 50:
        return "adaptation"
    else:
        return "dead"

REUSE_THRESHOLD_HOURS = 24


# Domain overrides for companies whose website doesn't match cleaned name
DOMAIN_OVERRIDES: dict[str, str] = {
    "cart.com": "cart.com",
    "peloton software": "peloton.com",
    "peloton": "onepeloton.com",
    "constant contact": "constantcontact.com",
    "surveymonkey": "surveymonkey.com",
    "hubspot": "hubspot.com",
    "servicenow": "servicenow.com",
    "crowdstrike": "crowdstrike.com",
    "palo alto networks": "paloaltonetworks.com",
    "toast": "toasttab.com",
    "bill.com": "bill.com",
    "monday.com": "monday.com",
    "five9": "five9.com",
    "8x8": "8x8.com",
    "wood mackenzie": "woodmac.com",
    "watchguard technologies": "watchguard.com",
    "watchguard": "watchguard.com",
}


def _logo(company_name: str) -> str:
    """Generate logo URL via Google Favicons — derive domain from company name."""
    lower = company_name.lower().strip()

    # Check overrides first
    if lower in DOMAIN_OVERRIDES:
        return f"https://www.google.com/s2/favicons?domain={DOMAIN_OVERRIDES[lower]}&sz=128"

    # Fallback: strip non-alphanumeric, append .com
    clean = lower.replace(" ", "").replace(",", "").replace("'", "")
    # Preserve dots in domain-like names (e.g. "cart.com" stays "cart.com")
    if clean.endswith(".com") or clean.endswith(".io") or clean.endswith(".ai"):
        domain = clean
    else:
        clean = clean.replace(".", "")
        domain = f"{clean}.com"
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"


class CohortService:
    def __init__(self, claude_client: ClaudeClient):
        self._claude = claude_client
        self._active_tasks: dict[int, asyncio.Task] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    async def create_cohort(
        self, name: str, company_names: list[str], db: AsyncSession
    ) -> dict:
        """Create a cohort and kick off background batch analysis."""
        # Deduplicate and clean names
        seen = set()
        clean_names: list[str] = []
        for n in company_names:
            stripped = n.strip()
            if stripped and stripped.lower() not in seen:
                seen.add(stripped.lower())
                clean_names.append(stripped)

        cohort = Cohort(
            name=name,
            status="analyzing",
            total_companies=len(clean_names),
            completed_companies=0,
            current_company=clean_names[0] if clean_names else None,
        )
        db.add(cohort)
        await db.commit()
        await db.refresh(cohort)

        # Launch background task
        task = asyncio.create_task(self._analyze_batch(cohort.id, clean_names))
        self._active_tasks[cohort.id] = task

        return self._cohort_to_dict(cohort)

    async def list_cohorts(self, db: AsyncSession) -> list[dict]:
        """Return all cohorts ordered by most recent first."""
        stmt = select(Cohort).order_by(Cohort.created_at.desc())
        result = await db.execute(stmt)
        return [self._cohort_to_dict(c) for c in result.scalars().all()]

    async def get_cohort_detail(self, cohort_id: int, db: AsyncSession) -> dict | None:
        """Get cohort metadata + all member evaluations for the summary table."""
        cohort = await db.get(Cohort, cohort_id)
        if not cohort:
            return None

        stmt = (
            select(CohortMember, Evaluation)
            .join(Evaluation, CohortMember.evaluation_id == Evaluation.id)
            .where(CohortMember.cohort_id == cohort_id)
            .order_by(CohortMember.position)
        )
        result = await db.execute(stmt)
        rows = result.all()

        zone_order = {"fortress": 0, "adaptation": 1, "compression": 2, "dead": 3}

        members = []
        for member, evaluation in rows:
            diligence = json.loads(evaluation.diligence) if evaluation.diligence else []
            overview = evaluation.overview or ""
            score_factors = None
            if evaluation.score_factors:
                try:
                    score_factors = json.loads(evaluation.score_factors)
                except (json.JSONDecodeError, TypeError):
                    pass
            members.append({
                "evaluation_id": evaluation.id,
                "company_name": evaluation.company_name,
                "zone": derive_zone(evaluation.x_score, evaluation.y_score),
                "x_score": evaluation.x_score,
                "y_score": evaluation.y_score,
                "score_factors": score_factors,
                "key_risk": diligence[0] if diligence else "N/A",
                "ai_summary": (overview[:150] + "...") if len(overview) > 150 else overview,
            })

        members.sort(key=lambda m: zone_order.get(m["zone"], 99))

        d = self._cohort_to_dict(cohort)
        d["members"] = members
        return d

    async def get_cohort_matrix(self, cohort_id: int, db: AsyncSession) -> list[dict]:
        """Return cohort members formatted as ReferenceCompany[] for MatrixChart."""
        stmt = (
            select(CohortMember, Evaluation)
            .join(Evaluation, CohortMember.evaluation_id == Evaluation.id)
            .where(CohortMember.cohort_id == cohort_id)
            .order_by(CohortMember.position)
        )
        result = await db.execute(stmt)
        rows = result.all()

        companies = []
        for member, evaluation in rows:
            justification = evaluation.justification or ""
            sentences = [s.strip() for s in justification.split(". ") if s.strip()]
            bullets = [
                s + ("." if not s.endswith(".") else "")
                for s in sentences[:3]
            ]

            companies.append({
                "name": evaluation.company_name,
                "ticker": evaluation.company_name[:4].upper(),
                "zone": derive_zone(evaluation.x_score, evaluation.y_score),
                "x": evaluation.x_score,
                "y": evaluation.y_score,
                "bullets": bullets or ["No justification available"],
                "logo_url": _logo(evaluation.company_name),
                "is_cohort": True,
            })

        return companies

    async def edit_cohort(
        self,
        cohort_id: int,
        add_companies: list[str],
        remove_eval_ids: list[int],
        db: AsyncSession,
    ) -> dict | None:
        """Edit a completed cohort — remove members and/or add new companies."""
        cohort = await db.get(Cohort, cohort_id)
        if not cohort:
            return None

        if cohort.status not in ("complete", "error"):
            raise ValueError("Can only edit completed or errored cohorts")

        # ── Remove members ──────────────────────────────────────────────────────
        if remove_eval_ids:
            stmt = (
                select(CohortMember)
                .where(CohortMember.cohort_id == cohort_id)
                .where(CohortMember.evaluation_id.in_(remove_eval_ids))
            )
            result = await db.execute(stmt)
            for member in result.scalars().all():
                await db.delete(member)

            cohort.total_companies -= len(remove_eval_ids)
            cohort.completed_companies = max(0, cohort.completed_companies - len(remove_eval_ids))
            await db.commit()

        # ── Add new companies ───────────────────────────────────────────────────
        if add_companies:
            # Deduplicate against existing members
            existing_stmt = (
                select(Evaluation.company_name)
                .join(CohortMember, CohortMember.evaluation_id == Evaluation.id)
                .where(CohortMember.cohort_id == cohort_id)
            )
            existing_result = await db.execute(existing_stmt)
            existing_names = {r[0].lower() for r in existing_result.all()}

            # Clean and deduplicate new names
            seen = set(existing_names)
            clean_new: list[str] = []
            for n in add_companies:
                stripped = n.strip()
                if stripped and stripped.lower() not in seen:
                    seen.add(stripped.lower())
                    clean_new.append(stripped)

            if clean_new:
                # Get max position for appending
                pos_stmt = (
                    select(func.max(CohortMember.position))
                    .where(CohortMember.cohort_id == cohort_id)
                )
                pos_result = await db.execute(pos_stmt)
                max_pos = pos_result.scalar() or 0
                start_pos = max_pos + 1

                # Update cohort status for re-analysis
                cohort.status = "analyzing"
                cohort.total_companies += len(clean_new)
                cohort.current_company = clean_new[0]
                await db.commit()
                await db.refresh(cohort)

                # Launch background task for just the new companies
                task = asyncio.create_task(
                    self._analyze_batch_append(cohort_id, clean_new, start_pos)
                )
                self._active_tasks[cohort_id] = task

        return await self.get_cohort_detail(cohort_id, db)

    async def delete_cohort(self, cohort_id: int, db: AsyncSession) -> bool:
        """Delete cohort + member links (keeps the evaluations)."""
        cohort = await db.get(Cohort, cohort_id)
        if not cohort:
            return False

        # Cancel running task if any
        task = self._active_tasks.pop(cohort_id, None)
        if task and not task.done():
            task.cancel()

        # Delete members
        stmt = select(CohortMember).where(CohortMember.cohort_id == cohort_id)
        result = await db.execute(stmt)
        for member in result.scalars().all():
            await db.delete(member)

        await db.delete(cohort)
        await db.commit()
        return True

    # ── Background batch analysis ─────────────────────────────────────────────

    async def _analyze_batch(self, cohort_id: int, company_names: list[str]):
        """Analyze each company sequentially — runs as background asyncio task."""
        for i, company_name in enumerate(company_names):
            async with async_session() as db:
                try:
                    # Update progress: current company
                    cohort = await db.get(Cohort, cohort_id)
                    if not cohort:
                        return
                    cohort.current_company = company_name
                    await db.commit()

                    # Check for a recent existing evaluation (< 24h)
                    cutoff = datetime.now(timezone.utc) - timedelta(hours=REUSE_THRESHOLD_HOURS)
                    stmt = (
                        select(Evaluation)
                        .where(func.lower(Evaluation.company_name) == company_name.lower())
                        .where(Evaluation.created_at >= cutoff)
                        .order_by(Evaluation.created_at.desc())
                        .limit(1)
                    )
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
                        logger.info(
                            f"Cohort {cohort_id}: reusing existing evaluation for {company_name}"
                        )
                        evaluation = existing
                    else:
                        logger.info(
                            f"Cohort {cohort_id}: analyzing {company_name} ({i+1}/{len(company_names)})"
                        )
                        raw = await self._claude.analyze_company(company_name)
                        # Build score_factors JSON with question-level detail
                        sf = None
                        x_f = raw.get("x_factors")
                        y_f = raw.get("y_factors")
                        x_detail = raw.get("x_detail")
                        y_detail = raw.get("y_detail")
                        inv_sentiment = raw.get("investment_sentiment")
                        # Clamp sub-factors and recalculate scores
                        x_f_clamped = {k: max(0, min(20, v)) for k, v in (x_f or {}).items()}
                        y_f_clamped = {k: max(0, min(20, v)) for k, v in (y_f or {}).items()}
                        if x_f or y_f:
                            factors_data = {"x_factors": x_f_clamped, "y_factors": y_f_clamped}
                            if x_detail:
                                factors_data["x_detail"] = x_detail
                            if y_detail:
                                factors_data["y_detail"] = y_detail
                            if inv_sentiment:
                                factors_data["investment_sentiment"] = inv_sentiment
                            sf = json.dumps(factors_data)
                        x_sc = sum(x_f_clamped.values()) if x_f_clamped else max(0, min(100, raw.get("x_score", 50)))
                        y_sc = sum(y_f_clamped.values()) if y_f_clamped else max(0, min(100, raw.get("y_score", 50)))

                        evaluation = Evaluation(
                            company_name=raw.get("company_name", company_name),
                            zone=derive_zone(x_sc, y_sc),
                            overview=raw.get("overview", ""),
                            justification=raw.get("justification", ""),
                            diligence=json.dumps(raw.get("diligence", [])),
                            x_score=x_sc,
                            y_score=y_sc,
                            score_factors=sf,
                        )
                        db.add(evaluation)
                        await db.commit()
                        await db.refresh(evaluation)

                    # Create cohort member link
                    member = CohortMember(
                        cohort_id=cohort_id,
                        evaluation_id=evaluation.id,
                        position=i,
                    )
                    db.add(member)

                    # Update progress
                    cohort = await db.get(Cohort, cohort_id)
                    cohort.completed_companies = i + 1
                    await db.commit()

                except Exception as e:
                    logger.error(
                        f"Cohort {cohort_id}: failed to analyze {company_name}: {e}"
                    )
                    # Continue to next company

            # Small delay between API calls to avoid rate limits
            await asyncio.sleep(1)

        # Mark complete
        async with async_session() as db:
            cohort = await db.get(Cohort, cohort_id)
            if cohort:
                cohort.status = "complete"
                cohort.current_company = None
                await db.commit()

        self._active_tasks.pop(cohort_id, None)
        logger.info(f"Cohort {cohort_id}: batch analysis complete")

    async def _analyze_batch_append(
        self, cohort_id: int, company_names: list[str], start_pos: int
    ):
        """Analyze new companies and append them to an existing cohort."""
        for i, company_name in enumerate(company_names):
            async with async_session() as db:
                try:
                    # Update progress: current company
                    cohort = await db.get(Cohort, cohort_id)
                    if not cohort:
                        return
                    cohort.current_company = company_name
                    await db.commit()

                    # Check for a recent existing evaluation (< 24h)
                    cutoff = datetime.now(timezone.utc) - timedelta(hours=REUSE_THRESHOLD_HOURS)
                    stmt = (
                        select(Evaluation)
                        .where(func.lower(Evaluation.company_name) == company_name.lower())
                        .where(Evaluation.created_at >= cutoff)
                        .order_by(Evaluation.created_at.desc())
                        .limit(1)
                    )
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
                        logger.info(
                            f"Cohort {cohort_id}: reusing existing evaluation for {company_name}"
                        )
                        evaluation = existing
                    else:
                        logger.info(
                            f"Cohort {cohort_id}: analyzing new addition {company_name}"
                        )
                        raw = await self._claude.analyze_company(company_name)
                        # Build score_factors JSON with question-level detail
                        sf = None
                        x_f = raw.get("x_factors")
                        y_f = raw.get("y_factors")
                        x_detail = raw.get("x_detail")
                        y_detail = raw.get("y_detail")
                        inv_sentiment = raw.get("investment_sentiment")
                        # Clamp sub-factors and recalculate scores
                        x_f_clamped = {k: max(0, min(20, v)) for k, v in (x_f or {}).items()}
                        y_f_clamped = {k: max(0, min(20, v)) for k, v in (y_f or {}).items()}
                        if x_f or y_f:
                            factors_data = {"x_factors": x_f_clamped, "y_factors": y_f_clamped}
                            if x_detail:
                                factors_data["x_detail"] = x_detail
                            if y_detail:
                                factors_data["y_detail"] = y_detail
                            if inv_sentiment:
                                factors_data["investment_sentiment"] = inv_sentiment
                            sf = json.dumps(factors_data)
                        x_sc = sum(x_f_clamped.values()) if x_f_clamped else max(0, min(100, raw.get("x_score", 50)))
                        y_sc = sum(y_f_clamped.values()) if y_f_clamped else max(0, min(100, raw.get("y_score", 50)))

                        evaluation = Evaluation(
                            company_name=raw.get("company_name", company_name),
                            zone=derive_zone(x_sc, y_sc),
                            overview=raw.get("overview", ""),
                            justification=raw.get("justification", ""),
                            diligence=json.dumps(raw.get("diligence", [])),
                            x_score=x_sc,
                            y_score=y_sc,
                            score_factors=sf,
                        )
                        db.add(evaluation)
                        await db.commit()
                        await db.refresh(evaluation)

                    # Create cohort member link
                    member = CohortMember(
                        cohort_id=cohort_id,
                        evaluation_id=evaluation.id,
                        position=start_pos + i,
                    )
                    db.add(member)

                    # Update progress
                    cohort = await db.get(Cohort, cohort_id)
                    cohort.completed_companies += 1
                    await db.commit()

                except Exception as e:
                    logger.error(
                        f"Cohort {cohort_id}: failed to analyze {company_name}: {e}"
                    )

            # Small delay between API calls to avoid rate limits
            await asyncio.sleep(1)

        # Mark complete
        async with async_session() as db:
            cohort = await db.get(Cohort, cohort_id)
            if cohort:
                cohort.status = "complete"
                cohort.current_company = None
                await db.commit()

        self._active_tasks.pop(cohort_id, None)
        logger.info(f"Cohort {cohort_id}: append analysis complete")

    async def get_cohort_report_data(self, cohort_id: int, db: AsyncSession) -> dict | None:
        """Fetch all data needed for PDF report generation (full evaluations)."""
        cohort = await db.get(Cohort, cohort_id)
        if not cohort or cohort.status != "complete":
            return None

        stmt = (
            select(CohortMember, Evaluation)
            .join(Evaluation, CohortMember.evaluation_id == Evaluation.id)
            .where(CohortMember.cohort_id == cohort_id)
            .order_by(CohortMember.position)
        )
        result = await db.execute(stmt)
        rows = result.all()

        members = []
        evaluations = []
        for member, evaluation in rows:
            diligence = json.loads(evaluation.diligence) if evaluation.diligence else []
            overview = evaluation.overview or ""
            score_factors = None
            if evaluation.score_factors:
                try:
                    score_factors = json.loads(evaluation.score_factors)
                except (json.JSONDecodeError, TypeError):
                    pass

            members.append({
                "evaluation_id": evaluation.id,
                "company_name": evaluation.company_name,
                "zone": derive_zone(evaluation.x_score, evaluation.y_score),
                "x_score": evaluation.x_score,
                "y_score": evaluation.y_score,
                "score_factors": score_factors,
                "key_risk": diligence[0] if diligence else "N/A",
                "ai_summary": (overview[:150] + "...") if len(overview) > 150 else overview,
            })

            evaluations.append({
                "id": evaluation.id,
                "company_name": evaluation.company_name,
                "zone": derive_zone(evaluation.x_score, evaluation.y_score),
                "overview": evaluation.overview or "",
                "justification": evaluation.justification or "",
                "diligence": diligence,
                "x_score": evaluation.x_score,
                "y_score": evaluation.y_score,
                "score_factors": score_factors,
            })

        return {
            "cohort_name": cohort.name,
            "cohort_created_at": cohort.created_at.isoformat() if cohort.created_at else None,
            "members": members,
            "evaluations": evaluations,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _cohort_to_dict(cohort: Cohort) -> dict:
        return {
            "id": cohort.id,
            "name": cohort.name,
            "status": cohort.status,
            "total_companies": cohort.total_companies,
            "completed_companies": cohort.completed_companies,
            "current_company": cohort.current_company,
            "created_at": cohort.created_at.isoformat() if cohort.created_at else None,
        }
