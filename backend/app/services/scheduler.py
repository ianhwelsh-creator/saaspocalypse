"""APScheduler for periodic background tasks."""

import logging
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, news_aggregator, stock_service, interval_minutes: int = 15):
        self._news = news_aggregator
        self._stocks = stock_service
        self._interval = interval_minutes
        self._scheduler = AsyncIOScheduler()

    def start(self):
        self._scheduler.add_job(
            self._refresh_news,
            "interval",
            minutes=self._interval,
            id="refresh_news",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info(f"Scheduler started (refresh every {self._interval} min)")

    def stop(self):
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    async def _refresh_news(self):
        try:
            await self._news.refresh_news()
            await self._news.refresh_fundraising()
            logger.info("Scheduled news refresh complete")
        except Exception as e:
            logger.error(f"Scheduled news refresh failed: {e}")
