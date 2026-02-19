"""SQLAlchemy ORM models."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    ticker: Mapped[str | None] = mapped_column(String, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CachedNewsItem(Base):
    __tablename__ = "cached_news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    zone: Mapped[str] = mapped_column(String, nullable=False)
    overview: Mapped[str] = mapped_column(Text, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    diligence: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    x_score: Mapped[float] = mapped_column(Float, nullable=False)
    y_score: Mapped[float] = mapped_column(Float, nullable=False)
    score_factors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: {x_factors, y_factors}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Cohort(Base):
    __tablename__ = "cohorts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|analyzing|complete|error
    total_companies: Mapped[int] = mapped_column(Integer, default=0)
    completed_companies: Mapped[int] = mapped_column(Integer, default=0)
    current_company: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CohortMember(Base):
    __tablename__ = "cohort_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cohort_id: Mapped[int] = mapped_column(Integer, nullable=False)
    evaluation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
