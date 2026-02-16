"""yfinance wrapper for stock data. Sync library wrapped with asyncio.to_thread."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

import yfinance as yf

logger = logging.getLogger(__name__)


class StockClient:
    def __init__(self, cache_ttl_minutes: int = 15):
        self._cache: dict[str, tuple[dict, datetime]] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)

    def _is_cached(self, key: str) -> bool:
        if key not in self._cache:
            return False
        _, ts = self._cache[key]
        return datetime.now(timezone.utc) - ts < self._cache_ttl

    def _get_cached(self, key: str) -> dict | None:
        if self._is_cached(key):
            return self._cache[key][0]
        return None

    def _set_cache(self, key: str, data: dict):
        self._cache[key] = (data, datetime.now(timezone.utc))

    async def get_historical_prices(
        self, tickers: list[str], start_date: str, end_date: str | None = None
    ) -> dict[str, list[dict]]:
        """Fetch daily close prices for tickers from start_date to end_date."""
        cache_key = f"hist_{'_'.join(sorted(tickers))}_{start_date}_{end_date}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        result = await asyncio.to_thread(
            self._fetch_historical, tickers, start_date, end_date
        )
        self._set_cache(cache_key, result)
        return result

    def _fetch_historical(
        self, tickers: list[str], start_date: str, end_date: str | None
    ) -> dict[str, list[dict]]:
        """Sync yfinance call — runs in thread pool."""
        try:
            ticker_str = " ".join(tickers)
            data = yf.download(
                ticker_str,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True,
            )

            if data.empty:
                logger.warning(f"No data returned for {tickers}")
                return {}

            result: dict[str, list[dict]] = {}
            close = data["Close"] if "Close" in data.columns or hasattr(data.columns, "levels") else data

            for ticker in tickers:
                try:
                    if len(tickers) == 1:
                        series = close
                    else:
                        series = close[ticker]

                    prices = []
                    for date, price in series.dropna().items():
                        prices.append({
                            "date": date.strftime("%Y-%m-%d"),
                            "close": round(float(price), 2),
                        })
                    result[ticker] = prices
                except (KeyError, AttributeError) as e:
                    logger.warning(f"Failed to get data for {ticker}: {e}")
                    result[ticker] = []

            return result
        except Exception as e:
            logger.error(f"yfinance download failed: {e}")
            return {}

    async def get_current_price(self, ticker: str) -> dict | None:
        """Get current price info for a single ticker."""
        cache_key = f"current_{ticker}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        result = await asyncio.to_thread(self._fetch_current, ticker)
        if result:
            self._set_cache(cache_key, result)
        return result

    def _fetch_current(self, ticker: str) -> dict | None:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            return {
                "ticker": ticker,
                "name": info.get("shortName", ticker),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
                "change_pct": info.get("regularMarketChangePercent", 0),
            }
        except Exception as e:
            logger.error(f"Failed to fetch current price for {ticker}: {e}")
            return None
