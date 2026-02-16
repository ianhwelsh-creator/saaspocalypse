"""Newsletter generation and email API endpoints."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import NewsletterRequest, NewsletterPreview, SendEmailRequest
from app.routers._deps import get_newsletter_service

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])


@router.post("/generate", response_model=NewsletterPreview)
async def generate_newsletter(req: NewsletterRequest):
    """Generate a newsletter preview from recent news."""
    service = get_newsletter_service()
    if not service:
        raise HTTPException(status_code=503, detail="Newsletter service not configured")
    return await service.generate(
        time_range_days=req.time_range_days,
        topics=req.topics or None,
        tone=req.tone,
    )


@router.post("/send")
async def send_newsletter(req: SendEmailRequest):
    """Send the newsletter via email."""
    service = get_newsletter_service()
    if not service:
        raise HTTPException(status_code=503, detail="Newsletter service not configured")
    return await service.send(
        html=req.html,
        recipient_email=req.recipient_email,
        subject=req.subject,
    )
