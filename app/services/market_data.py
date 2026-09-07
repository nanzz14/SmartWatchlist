"""
Market data fetcher using Yahoo Finance (yfinance).

Provides:
- Live/historical stock quotes
- NIFTY 50 index data
- 52-week high/low
- SMA20 / SMA50
- 5-day return
- ATR-like volatility metrics
- Volume analysis
- Sparkline data
- Price/volume event detection
"""

from __future__ import annotations

import logging
import time
from datetime import timezone
from typing import Any, Dict, List, Optional

import yfinance as yf

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# CACHE
# ============================================================

_quote_cache: Dict[str, Dict[str, Any]] = {}

# Cache Yahoo responses for 2 minutes
TTL_SECONDS = 120

# If Yahoo rate-limits us, temporarily stop making requests
rate_limited_until = 0


# ============================================================
# HELPERS
# ============================================================

def _mean(values: List[float]) -> float:
    """Return average of a list of numbers."""
    if not values:
        return 0.0

    return sum(values) / len(values)


def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""
    try:
        value = float(value)

        # NaN check
        if value != value:
            return None

        return value

    except (TypeError, ValueError):
        return None


# ============================================================
# FETCH YAHOO QUOTE
# ============================================================

def fetch_yahoo_quote(
    yahoo_symbol: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch approximately 1 year of daily market data from Yahoo Finance.

    The 1-year window allows us to calculate:
        - 52-week high
        - 52-week low
        - SMA20
        - SMA50
        - 5-day return
        - volume metrics
        - volatility metrics
        - sparkline data
    """

    global rate_limited_until

    # Don't hit Yahoo if we are currently rate limited
    if time.time() < rate_limited_until:
        return None

    try:

        ticker = yf.Ticker(yahoo_symbol)

        # --------------------------------------------------------
        # IMPORTANT:
        # Use 1 year because we need true 52-week metrics
        # --------------------------------------------------------

        hist = ticker.history(
            period="1y",
            interval="1d"
        )

        if hist.empty or len(hist) < 5:
            logger.info(
                "No sufficient history for %s",
                yahoo_symbol
            )
            return None

        # --------------------------------------------------------
        # CLOSE PRICES
        # --------------------------------------------------------

        closes = [
            float(x)
            for x in hist["Close"].dropna().tolist()
        ]

        if len(closes) < 5:
            return None

        # --------------------------------------------------------
        # HIGH / LOW RANGE
        # Used for volatility calculations
        # --------------------------------------------------------

        ranges: List[float] = []

        for _, row in hist.iterrows():

            close = _safe_float(row["Close"])
            high = _safe_float(row["High"])
            low = _safe_float(row["Low"])

            if (
                close is not None
                and high is not None
                and low is not None
                and close > 0
            ):
                ranges.append(
                    (high - low) / close
                )

        # --------------------------------------------------------
        # VOLUMES
        # --------------------------------------------------------

        volumes = [
            float(x)
            for x in hist["Volume"].dropna().tolist()
            if float(x) > 0
        ]

        # --------------------------------------------------------
        # CURRENT PRICE
        # --------------------------------------------------------

        price = closes[-1]

        # Try to get the latest available market price
        # instead of relying only on the last daily candle.
        try:

            fast_info = ticker.fast_info

            if fast_info:

                live_price = fast_info.get(
                    "last_price"
                )

                if live_price is not None:
                    price = float(live_price)

        except Exception:
            # If fast_info fails, use last daily close
            pass

        # --------------------------------------------------------
        # PREVIOUS CLOSE
        # --------------------------------------------------------

        prev_close = closes[-2]

        # --------------------------------------------------------
        # TRUE 52-WEEK HIGH / LOW
        #
        # IMPORTANT:
        # Use High and Low columns instead of max/min Close.
        # --------------------------------------------------------

        high_values = [
            float(x)
            for x in hist["High"].dropna().tolist()
        ]

        low_values = [
            float(x)
            for x in hist["Low"].dropna().tolist()
        ]

        high_52 = max(high_values) if high_values else max(closes)
        low_52 = min(low_values) if low_values else min(closes)

        # --------------------------------------------------------
        # VOLUME
        # --------------------------------------------------------

        volume = (
            volumes[-1]
            if volumes
            else 0
        )

        # Average of last 20 trading days
        avg_volume = (
            _mean(volumes[-20:])
            if volumes
            else volume
        )

        # Volume ratio tells us whether today's volume
        # is unusually high.
        volume_ratio = (
            volume / avg_volume
            if avg_volume > 0
            else 1.0
        )

        # --------------------------------------------------------
        # MOVING AVERAGES
        # --------------------------------------------------------

        sma20 = _mean(closes[-20:])
        sma50 = _mean(closes[-50:])

        # --------------------------------------------------------
        # 5-DAY RETURN
        # --------------------------------------------------------

        ret_base = (
            closes[-6]
            if len(closes) >= 6
            else prev_close
        )

        ret5d = (
            ((price - ret_base) / ret_base) * 100
            if ret_base
            else 0
        )

        # --------------------------------------------------------
        # ATR-LIKE VOLATILITY
        # --------------------------------------------------------

        atr14 = (
            _mean(ranges[-14:]) * price
            if ranges
            else 0
        )

        avg_range20 = _mean(
            ranges[-20:]
        )

        range5 = _mean(
            ranges[-5:]
        )

        # --------------------------------------------------------
        # CLEAN SYMBOL
        # --------------------------------------------------------

        clean_symbol = yahoo_symbol.upper()

        if clean_symbol.endswith(".NS"):
            clean_symbol = clean_symbol[:-3]

        elif clean_symbol.endswith(".BO"):
            clean_symbol = clean_symbol[:-3]

        # --------------------------------------------------------
        # STOCK NAME
        # --------------------------------------------------------

        stock_name = clean_symbol

        try:

            info = ticker.info or {}

            stock_name = (
                info.get("shortName")
                or info.get("longName")
                or clean_symbol
            )

        except Exception:
            pass

        # --------------------------------------------------------
        # BUILD QUOTE
        # --------------------------------------------------------

        quote = {
            "symbol": clean_symbol,

            "yahoo": yahoo_symbol,

            "name": stock_name,

            "price": round(
                price,
                2
            ),

            "prevClose": round(
                prev_close,
                2
            ),

            "changePct": round(
                (
                    (price - prev_close)
                    / prev_close
                ) * 100,
                2
            ) if prev_close else 0,

            # True 52-week values
            "high52": round(
                high_52,
                2
            ),

            "low52": round(
                low_52,
                2
            ),

            # Volume
            "volume": int(volume),

            "avgVolume": int(avg_volume),

            "volumeRatio": round(
                volume_ratio,
                2
            ),

            # Moving averages
            "sma20": round(
                sma20,
                2
            ),

            "sma50": round(
                sma50,
                2
            ),

            # Returns
            "ret5d": round(
                ret5d,
                2
            ),

            # Volatility
            "atr14": round(
                atr14,
                2
            ),

            "avgRange20": round(
                avg_range20,
                4
            ),

            "range5": round(
                range5,
                4
            ),

            # Last 48 observations for frontend sparkline
            "spark": [
                round(x, 2)
                for x in closes[-48:]
            ],

            "currency": "INR"
        }

        return quote

    except Exception as exc:

        # If Yahoo gives us a rate-limit error,
        # pause requests for 60 seconds.
        if "429" in str(exc):
            rate_limited_until = (
                time.time() + 60
            )

        logger.warning(
            "Yahoo quote error for %s: %s",
            yahoo_symbol,
            exc
        )

        return None


# ============================================================
# GET QUOTE WITH CACHE
# ============================================================

def get_quote(
    stock_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get a stock quote.

    Flow:

        1. Resolve stock -> Yahoo ticker
        2. Check cache
        3. Fetch Yahoo if cache expired
        4. Save fresh result
        5. Return cached result if Yahoo fails
    """

    stock_id = stock_id.upper().strip()

    # --------------------------------------------------------
    # Resolve Yahoo symbol
    # --------------------------------------------------------

    if stock_id in settings.YAHOO_SYMBOL_MAP:
        yahoo_symbol = settings.YAHOO_SYMBOL_MAP[stock_id]
    elif "." in stock_id or stock_id.startswith("^") or stock_id in ("AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"):
        yahoo_symbol = stock_id
    else:
        # Default Indian Stock Exchange ticker (.NS)
        yahoo_symbol = f"{stock_id}.NS"


    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    cached = _quote_cache.get(
        yahoo_symbol
    )

    if cached:

        age = (
            time.time()
            - cached["at"]
        )

        if age < TTL_SECONDS:
            return cached["quote"]

    # --------------------------------------------------------
    # FETCH FROM YAHOO
    # --------------------------------------------------------

    quote = fetch_yahoo_quote(
        yahoo_symbol
    )

    if quote:

        # Make sure our internal symbol is preserved
        quote["symbol"] = stock_id

        _quote_cache[yahoo_symbol] = {
            "at": time.time(),
            "quote": quote
        }

        return quote

    # --------------------------------------------------------
    # FALLBACK TO OLD CACHE
    # --------------------------------------------------------

    if cached:
        return cached["quote"]

    return None


# ============================================================
# FETCH PRICE EVENTS
# ============================================================

def fetch_price_events(
    stock_id: str,
    period: str = "5d",
    pct_threshold: float = 0.4,
    volume_spike_ratio: float = 1.3,
    interval: str = "1d",
) -> List[Dict[str, Any]]:
    """
    Fetch recent price & volume data and detect noteworthy events.

    Default:
        period = 5d
        interval = 1d

    This is more stable for the Smart Watchlist than using
    1-minute candles by default.

    For a live intraday demo, you can still call:

        fetch_price_events(
            "RELIANCE",
            period="1d",
            interval="1m"
        )
    """

    try:

        clean_id = stock_id.upper().strip()
        if clean_id in settings.YAHOO_SYMBOL_MAP:
            yahoo_symbol = settings.YAHOO_SYMBOL_MAP[clean_id]
        elif "." in clean_id or clean_id.startswith("^") or clean_id in ("AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"):
            yahoo_symbol = clean_id
        else:
            yahoo_symbol = f"{clean_id}.NS"


        ticker = yf.Ticker(
            yahoo_symbol
        )

        hist = ticker.history(
            period=period,
            interval=interval
        )

        if hist.empty:

            # Fallback to daily data
            hist = ticker.history(
                period="5d",
                interval="1d"
            )

            pct_threshold = max(
                pct_threshold,
                1.5
            )

    except Exception as exc:

        logger.warning(
            "yfinance error for %s: %s",
            stock_id,
            exc
        )

        return []

    if hist.empty or len(hist) < 2:

        logger.info(
            "No sufficient history for %s",
            stock_id
        )

        return []

    # Keep latest 90 observations for 1-minute data
    # so we don't flood the event pipeline.
    if (
        interval == "1m"
        and len(hist) > 90
    ):
        hist = hist.iloc[-90:]

    # --------------------------------------------------------
    # AVERAGE VOLUME
    # --------------------------------------------------------

    volumes = [
        float(x)
        for x in hist["Volume"].dropna().tolist()
        if float(x) > 0
    ]

    avg_volume = (
        _mean(volumes)
        if volumes
        else 0
    )

    events: List[
        Dict[str, Any]
    ] = []

    # --------------------------------------------------------
    # DETECT EVENTS
    # --------------------------------------------------------

    for i in range(
        1,
        len(hist)
    ):

        row = hist.iloc[i]
        prev = hist.iloc[i - 1]

        current_close = _safe_float(
            row["Close"]
        )

        previous_close = _safe_float(
            prev["Close"]
        )

        current_volume = _safe_float(
            row["Volume"]
        )

        if (
            current_close is None
            or previous_close is None
            or previous_close == 0
        ):
            continue

        if current_volume is None:
            current_volume = 0

        # ----------------------------------------------------
        # PRICE CHANGE
        # ----------------------------------------------------

        pct_change = (
            (
                current_close
                - previous_close
            )
            / previous_close
        ) * 100

        # ----------------------------------------------------
        # VOLUME RATIO
        # ----------------------------------------------------

        volume_ratio = (
            current_volume / avg_volume
            if avg_volume > 0
            else 1.0
        )

        # ----------------------------------------------------
        # EVENT CONDITIONS
        #
        # Flag if:
        #   A significant price move occurs
        # OR
        #   A significant volume spike occurs
        # ----------------------------------------------------

        significant_move = (
            abs(pct_change)
            >= pct_threshold
        )

        volume_spike = (
            volume_ratio
            >= volume_spike_ratio
        )

        if not (
            significant_move
            or volume_spike
        ):
            continue

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        ts = row.name

        if hasattr(
            ts,
            "to_pydatetime"
        ):
            ts = ts.to_pydatetime()

        # Make timezone-aware
        if ts.tzinfo is None:
            ts = ts.replace(
                tzinfo=timezone.utc
            )

        # ----------------------------------------------------
        # EVENT TYPE
        # ----------------------------------------------------

        if (
            significant_move
            and volume_spike
        ):
            event_type = "price_and_volume"

        elif significant_move:
            event_type = "price_move"

        else:
            event_type = "volume_spike"

        # ----------------------------------------------------
        # EVENT
        # ----------------------------------------------------

        events.append({

            "stock_id": stock_id,

            "source": "yahoo",

            "timestamp": ts.isoformat(),

            "event_type": event_type,

            "payload": {

                "pct_change": round(
                    pct_change,
                    2
                ),

                "volume_ratio": round(
                    volume_ratio,
                    2
                ),

                "close": round(
                    current_close,
                    2
                ),

                "prev_close": round(
                    previous_close,
                    2
                ),

                "volume": int(
                    current_volume
                ),

                "avg_volume": int(
                    avg_volume
                )
            }
        })

    logger.info(
        "Found %d price events for %s",
        len(events),
        stock_id
    )

    return events


# ============================================================
# STOCK INFORMATION
# ============================================================

def fetch_stock_info(
    stock_id: str
) -> Dict[str, Any]:
    """
    Return basic stock information from Yahoo Finance.

    Useful for:
        - company name
        - sector
        - market cap
        - currency
        - current price
    """

    try:

        yahoo_symbol = (
            settings.YAHOO_SYMBOL_MAP.get(
                stock_id.upper(),
                stock_id
            )
        )

        ticker = yf.Ticker(
            yahoo_symbol
        )

        info = ticker.info or {}

        return {

            "short_name": info.get(
                "shortName",
                stock_id
            ),

            "long_name": info.get(
                "longName",
                stock_id
            ),

            "sector": info.get(
                "sector"
            ),

            "market_cap": info.get(
                "marketCap"
            ),

            "currency": info.get(
                "currency",
                "INR"
            ),

            "current_price": (
                info.get("currentPrice")
                or info.get(
                    "regularMarketPrice"
                )
            )
        }

    except Exception as exc:

        logger.warning(
            "yfinance info error for %s: %s",
            stock_id,
            exc
        )

        return {
            "short_name": stock_id,
            "long_name": stock_id
        }


# ============================================================
# FETCH MARKET
# ============================================================

def fetch_market(
    symbols: List[str]
) -> Dict[str, Any]:
    """
    Fetch market data for multiple watchlist stocks.

    Example:

        fetch_market([
            "RELIANCE",
            "TCS",
            "INFY",
            "HDFCBANK"
        ])

    Returns:

        {
            "quotes": [...],
            "index": {...},
            "asOf": "...",
            "live": True
        }
    """

    # --------------------------------------------------------
    # NORMALIZE + REMOVE DUPLICATES
    # --------------------------------------------------------

    wanted = list(
        dict.fromkeys(
            symbol.upper().strip()
            for symbol in symbols
            if symbol
        )
    )

    # Protect Yahoo from excessive requests
    wanted = wanted[:24]

    quotes: List[
        Dict[str, Any]
    ] = []

    # --------------------------------------------------------
    # FETCH STOCKS
    # --------------------------------------------------------

    for symbol in wanted:

        quote = get_quote(
            symbol
        )

        if quote:
            quotes.append(
                quote
            )

    # --------------------------------------------------------
    # FETCH NIFTY 50
    # Yahoo ticker = ^NSEI
    # --------------------------------------------------------

    nifty = get_quote(
        "^NSEI"
    )

    if nifty:

        nifty["symbol"] = "NIFTY"

        nifty["name"] = "Nifty 50"

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "quotes": quotes,

        "index": nifty,

        "asOf": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime()
        ),

        "live": (
            time.time()
            >= rate_limited_until
        )
    }