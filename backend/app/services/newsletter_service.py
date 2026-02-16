"""Newsletter generation and email delivery service."""

import logging

from app.apis.claude_client import ClaudeClient
from app.apis.email_client import EmailClient
from app.services.news_aggregator import NewsAggregator

logger = logging.getLogger(__name__)


class NewsletterService:
    def __init__(
        self,
        claude_client: ClaudeClient,
        email_client: EmailClient,
        news_aggregator: NewsAggregator,
    ):
        self._claude = claude_client
        self._email = email_client
        self._news = news_aggregator

    async def generate(self, time_range_days: int = 7, topics: list[str] | None = None, tone: str = "professional") -> dict:
        """Generate newsletter from recent news."""
        news_items = await self._news.get_all_news(limit=50)

        if topics:
            news_items = [n for n in news_items if n.get("category") in topics]

        result = await self._claude.generate_newsletter(
            news_items=news_items,
            tone=tone,
            topics=topics,
        )

        return {
            "subject": result.get("subject", "SaaSpocalypse Weekly"),
            "html": result.get("html", "<p>No content generated</p>"),
        }

    async def send(self, html: str, recipient_email: str, subject: str) -> dict:
        """Send the newsletter via email."""
        return await self._email.send_email(
            to=recipient_email,
            subject=subject,
            html=html,
        )
