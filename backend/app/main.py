"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.apis.stock_client import StockClient
from app.apis.claude_client import ClaudeClient
from app.apis.arena_client import ArenaClient
from app.apis.twitter_client import TwitterClient
from app.apis.rss_client import RSSClient
from app.apis.email_client import EmailClient
from app.apis.institutional_client import InstitutionalClient
from app.services.arena_service import ArenaService
from app.services.news_aggregator import NewsAggregator
from app.services.newsletter_service import NewsletterService
from app.services.stock_service import StockService
from app.services.scheduler import Scheduler
from app.services.cohort_service import CohortService
from app.routers._deps import init_deps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()

    logger.info("Initializing API clients...")
    stock_client = StockClient(cache_ttl_minutes=settings.STOCK_CACHE_TTL_MINUTES)
    arena_client = ArenaClient()
    twitter_client = TwitterClient(bearer_token=settings.TWITTER_BEARER_TOKEN)
    rss_client = RSSClient()
    institutional_client = InstitutionalClient()

    claude_client = None
    if settings.ANTHROPIC_API_KEY:
        claude_client = ClaudeClient(api_key=settings.ANTHROPIC_API_KEY)

    email_client = EmailClient(api_key=settings.RESEND_API_KEY)

    # Build services
    arena_service = ArenaService(arena_client)
    news_aggregator = NewsAggregator(
        rss_client=rss_client,
        twitter_client=twitter_client,
        institutional_client=institutional_client,
        claude_client=claude_client,
    )

    newsletter_service = None
    if claude_client:
        newsletter_service = NewsletterService(
            claude_client=claude_client,
            email_client=email_client,
            news_aggregator=news_aggregator,
        )

    stock_service = StockService(stock_client)

    cohort_service = None
    if claude_client:
        cohort_service = CohortService(claude_client)

    init_deps(
        stock_client=stock_client,
        claude_client=claude_client,
        arena_service=arena_service,
        news_aggregator=news_aggregator,
        newsletter_service=newsletter_service,
        cohort_service=cohort_service,
    )

    # Start scheduler for periodic news refresh
    scheduler = Scheduler(
        news_aggregator=news_aggregator,
        stock_service=stock_service,
        interval_minutes=settings.NEWS_REFRESH_INTERVAL_MINUTES,
    )
    scheduler.start()

    # Initial data load (non-blocking so server starts immediately)
    import asyncio

    async def _initial_load():
        try:
            logger.info("Loading initial news data...")
            await news_aggregator.refresh_news()
            await news_aggregator.refresh_fundraising()
            logger.info("Initial news data loaded")
        except Exception as e:
            logger.error(f"Initial news load failed: {e}")

    asyncio.create_task(_initial_load())

    logger.info("SaaSpocalypse backend ready")
    yield

    # Shutdown
    scheduler.stop()
    await twitter_client.close()
    await rss_client.close()
    await arena_client.close()
    await institutional_client.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="SaaSpocalypse",
    description="SaaS AI disruption tracking dashboard",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import stocks, arena, news, watchlist, evaluator, newsletter, cohorts  # noqa

app.include_router(stocks.router)
app.include_router(arena.router)
app.include_router(news.router)
app.include_router(watchlist.router)
app.include_router(evaluator.router)
app.include_router(newsletter.router)
app.include_router(cohorts.router)
