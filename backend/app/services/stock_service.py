"""Stock basket calculations — equal-weight indexing to baseline."""

import logging
from datetime import datetime

from app.apis.stock_client import StockClient
from app.seed.baskets import BASKETS, BASELINE_DATE, TICKER_RATIONALE

logger = logging.getLogger(__name__)


class StockService:
    def __init__(self, client: StockClient):
        self._client = client

    async def get_basket_time_series(self, end_date: str | None = None) -> dict:
        """Get indexed time series for all baskets since baseline date."""
        all_tickers = []
        for basket in BASKETS.values():
            all_tickers.extend(basket["tickers"])

        prices = await self._client.get_historical_prices(
            tickers=all_tickers,
            start_date=BASELINE_DATE,
            end_date=end_date,
        )

        if not prices:
            return {"series": [], "summaries": [], "baseline_date": BASELINE_DATE}

        # Collect all unique dates across all tickers
        all_dates: set[str] = set()
        for ticker_prices in prices.values():
            for p in ticker_prices:
                all_dates.add(p["date"])
        sorted_dates = sorted(all_dates)

        if not sorted_dates:
            return {"series": [], "summaries": [], "baseline_date": BASELINE_DATE}

        # Build lookup: ticker -> date -> close
        price_lookup: dict[str, dict[str, float]] = {}
        for ticker, ticker_prices in prices.items():
            price_lookup[ticker] = {p["date"]: p["close"] for p in ticker_prices}

        # Find baseline prices (first available date >= BASELINE_DATE)
        baseline_prices: dict[str, float] = {}
        for ticker in all_tickers:
            if ticker not in price_lookup:
                continue
            for d in sorted_dates:
                if d >= BASELINE_DATE and d in price_lookup.get(ticker, {}):
                    price_at_date = price_lookup.get(ticker, {}).get(d)
                    if price_at_date:
                        baseline_prices[ticker] = price_at_date
                        break

        # Build time series
        series = []
        for date in sorted_dates:
            point = {"date": date}
            for zone_key, basket in BASKETS.items():
                indexed_values = []
                for ticker in basket["tickers"]:
                    close = price_lookup.get(ticker, {}).get(date)
                    base = baseline_prices.get(ticker)
                    if close and base and base > 0:
                        indexed_values.append((close / base) * 100)

                if indexed_values:
                    point[zone_key] = round(sum(indexed_values) / len(indexed_values), 2)

            series.append(point)

        # Build summaries (latest values)
        summaries = []
        for zone_key, basket in BASKETS.items():
            latest_value = None
            for point in reversed(series):
                if zone_key in point:
                    latest_value = point[zone_key]
                    break

            summaries.append({
                "zone": zone_key,
                "label": basket["label"],
                "current_value": latest_value or 100.0,
                "change_from_baseline": round((latest_value or 100.0) - 100, 2),
                "color": basket["color"],
                "tickers": basket["tickers"],
            })

        # Per-ticker % change from baseline for tooltips
        ticker_changes: dict[str, float] = {}
        for ticker in all_tickers:
            base = baseline_prices.get(ticker)
            if not base or base <= 0:
                continue
            # Find latest close for this ticker
            for d in reversed(sorted_dates):
                close = price_lookup.get(ticker, {}).get(d)
                if close:
                    ticker_changes[ticker] = round((close / base - 1) * 100, 2)
                    break

        return {
            "series": series,
            "summaries": summaries,
            "baseline_date": BASELINE_DATE,
            "ticker_rationale": TICKER_RATIONALE,
            "ticker_changes": ticker_changes,
        }

    async def get_basket_detail(self, zone: str) -> list[dict]:
        """Get individual stock details for a specific zone."""
        basket = BASKETS.get(zone)
        if not basket:
            return []

        details = []
        for ticker in basket["tickers"]:
            info = await self._client.get_current_price(ticker)
            if info:
                details.append(info)
            else:
                details.append({
                    "ticker": ticker,
                    "name": ticker,
                    "current_price": 0,
                    "change_pct": 0,
                })

        return details
