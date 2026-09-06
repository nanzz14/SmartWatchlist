"""
Free news feed fetcher using RSS (Google News + Moneycontrol).

No API key required.  Uses ``feedparser`` to parse RSS/Atom feeds
and returns headline-based event dicts ready for the tagging pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List
from urllib.parse import quote

import feedparser

from app.config import settings

logger = logging.getLogger(__name__)

# ── RSS feed URL templates ───────────────────────────────────────────────

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

# Moneycontrol general RSS — not stock-specific but useful for market news
MONEYCONTROL_RSS = "https://www.moneycontrol.com/rss/latestnews.xml"


def _parse_pub_date(entry: dict) -> datetime:
    """Extract a timezone-aware datetime from a feed entry."""
    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass
    return datetime.now(timezone.utc)


def _clean_title(title: str) -> str:
    """Strip trailing source attribution that Google News appends."""
    # Google News titles look like: "Headline text - Source Name"
    if " - " in title:
        return title.rsplit(" - ", 1)[0].strip()
    return title.strip()


# ── public API ───────────────────────────────────────────────────────────

def fetch_news_events(
    stock_id: str,
    max_items: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetch recent news headlines for a stock from Google News RSS.

    Parameters
    ----------
    stock_id : str
        Yahoo Finance ticker, e.g. ``"RELIANCE.NS"``
    max_items : int
        Maximum number of headlines to return.

    Returns
    -------
    list[dict]
        Raw event dicts with ``payload.headline`` set, ready for
        ``tag_event()``.
    """
    # Resolve a human-readable search query for the ticker
    search_name = settings.STOCK_NAME_MAP.get(
        stock_id.upper(),
        stock_id.replace(".NS", "").replace(".BO", ""),
    )

    query = quote(f"{search_name} stock")
    url = GOOGLE_NEWS_RSS.format(query=query)

    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        logger.warning("RSS fetch error for %s: %s", stock_id, exc)
        return []

    events: List[Dict[str, Any]] = []
    for entry in feed.entries[:max_items]:
        title = _clean_title(entry.get("title", ""))
        if not title:
            continue

        pub_date = _parse_pub_date(entry)
        link = entry.get("link", "")

        events.append({
            "stock_id": stock_id,
            "source": "google_news_rss",
            "timestamp": pub_date.isoformat(),
            "payload": {
                "headline": title,
                "url": link,
                "source_feed": "google_news",
            },
        })

    logger.info("Found %d news items for %s", len(events), stock_id)
    return events


def fetch_market_news(max_items: int = 15) -> List[Dict[str, Any]]:
    """
    Fetch general Indian market news from Moneycontrol RSS.
    These are not stock-specific but can still be matched via relevance
    scoring.
    """
    try:
        feed = feedparser.parse(MONEYCONTROL_RSS)
    except Exception as exc:
        logger.warning("Moneycontrol RSS error: %s", exc)
        return []

    events: List[Dict[str, Any]] = []
    for entry in feed.entries[:max_items]:
        title = entry.get("title", "").strip()
        if not title:
            continue

        pub_date = _parse_pub_date(entry)
        link = entry.get("link", "")

        events.append({
            "stock_id": "MARKET",  # will be matched to watchlisted stocks via keywords
            "source": "moneycontrol_rss",
            "timestamp": pub_date.isoformat(),
            "payload": {
                "headline": title,
                "url": link,
                "source_feed": "moneycontrol",
            },
        })

    logger.info("Found %d general market news items", len(events))
    return events
