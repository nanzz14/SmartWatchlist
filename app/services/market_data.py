"""
Live market data fetcher using Yahoo Finance (yfinance).

Detects significant price moves and volume spikes for watchlisted stocks
and returns raw event dicts ready for the tagging pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_price_events(
    stock_id: str,
    period: str = "1d",
    pct_threshold: float = 0.4,
    volume_spike_ratio: float = 1.3,
    interval: str = "1m",
) -> List[Dict[str, Any]]:
    """
    Fetch recent price & volume data from Yahoo Finance and detect
    noteworthy moves.

    Parameters
    ----------
    stock_id : str
        Yahoo Finance ticker, e.g. ``"RELIANCE.NS"``
    period : str
        Lookback window accepted by yfinance (``"1d"``, ``"5d"``, ``"1mo"``…)
    pct_threshold : float
        Minimum absolute daily % change to flag as an event.
    volume_spike_ratio : float
        A day's volume must exceed ``avg_volume × ratio`` to count as a
        volume spike.

    Returns
    -------
    list[dict]
        Raw event dicts with keys expected by ``tag_event()``.
    """
    try:
        ticker = yf.Ticker(stock_id)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            hist = ticker.history(period="5d", interval="1d")
            pct_threshold = max(pct_threshold, 1.5)
    except Exception as exc:
        logger.warning("yfinance error for %s: %s", stock_id, exc)
        return []

    if hist.empty or len(hist) < 2:
        logger.info("No sufficient history for %s", stock_id)
        return []

    # Keep the latest window so 1-minute bars don't flood the digest
    if interval == "1m" and len(hist) > 90:
        hist = hist.iloc[-90:]

    avg_volume = hist["Volume"].mean()
    events: List[Dict[str, Any]] = []

    for i in range(1, len(hist)):
        row = hist.iloc[i]
        prev = hist.iloc[i - 1]

        if prev["Close"] == 0:
            continue

        pct_change = ((row["Close"] - prev["Close"]) / prev["Close"]) * 100
        volume_ratio = row["Volume"] / avg_volume if avg_volume > 0 else 1.0

        # Only flag if the move exceeds our threshold
        if abs(pct_change) < pct_threshold:
            continue

        ts = row.name  # pandas Timestamp index
        if hasattr(ts, "to_pydatetime"):
            ts = ts.to_pydatetime()
        # Ensure timezone-aware
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        events.append({
            "stock_id": stock_id,
            "source": "yahoo",
            "timestamp": ts.isoformat(),
            "payload": {
                "pct_change": round(pct_change, 2),
                "volume_ratio": round(volume_ratio, 2),
                "close": round(row["Close"], 2),
                "prev_close": round(prev["Close"], 2),
                "volume": int(row["Volume"]),
                "avg_volume": int(avg_volume),
            },
        })

    logger.info("Found %d price events for %s", len(events), stock_id)
    return events


def fetch_stock_info(stock_id: str) -> Dict[str, Any]:
    """
    Return basic stock info (name, sector, market cap, etc.) from Yahoo
    Finance.  Useful for display purposes and for enriching news queries.
    """
    try:
        ticker = yf.Ticker(stock_id)
        info = ticker.info or {}
        return {
            "short_name": info.get("shortName", stock_id),
            "long_name": info.get("longName", stock_id),
            "sector": info.get("sector"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        }
    except Exception as exc:
        logger.warning("yfinance info error for %s: %s", stock_id, exc)
        return {"short_name": stock_id, "long_name": stock_id}
