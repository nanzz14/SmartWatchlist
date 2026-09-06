"""
Seed script: creates demo user + theses, then fetches LIVE data
from Yahoo Finance (price/volume) and Google News RSS (headlines).

Usage:
    python -m scripts.seed_data
"""

from datetime import datetime, timezone

from app.database import SessionLocal, engine, Base
from app.models import Event, RelevanceScore, Thesis, User, WatchlistItem
from app.services.market_data import fetch_price_events
from app.services.news_feed import fetch_news_events
from app.services.relevance import calculate_relevance
from app.services.tagging import tag_event

# ── bootstrap ────────────────────────────────────────────────────────────

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clean start
db.query(RelevanceScore).delete()
db.query(Event).delete()
db.query(Thesis).delete()
db.query(WatchlistItem).delete()
db.query(User).delete()
db.commit()
print("🗑️  Cleared old data")

# ── Demo user ────────────────────────────────────────────────────────────

user = User(id=1, name="Demo User")
db.add(user)
db.commit()
print("👤 Created Demo User")

# ── Thesis 1 – Reliance (margin expansion focused) ──────────────────────

item1 = WatchlistItem(user_id=1, stock_id="RELIANCE.NS")
db.add(item1)
db.flush()
thesis1 = Thesis(
    watchlist_item_id=item1.id,
    tags=["margin_expansion", "earnings", "oil"],
    free_text="Looking for sustained margin expansion in refining and retail",
)
db.add(thesis1)
print("📋 Thesis 1: RELIANCE.NS — margin expansion, earnings, oil")

# ── Thesis 2 – TCS (growth + talent) ────────────────────────────────────

item2 = WatchlistItem(user_id=1, stock_id="TCS.NS")
db.add(item2)
db.flush()
thesis2 = Thesis(
    watchlist_item_id=item2.id,
    tags=["growth", "deal_wins", "management"],
    free_text="Want large deal wins and stable attrition",
)
db.add(thesis2)
db.commit()
print("📋 Thesis 2: TCS.NS — growth, deal wins, management")

# ── Fetch LIVE events ───────────────────────────────────────────────────

stocks = ["RELIANCE.NS", "TCS.NS"]
total_events = 0

for stock_id in stocks:
    print(f"\n🔄 Fetching live data for {stock_id}...")

    # Yahoo Finance — price & volume
    price_events = fetch_price_events(stock_id, period="5d", pct_threshold=1.0)
    print(f"   📈 {len(price_events)} price events from Yahoo Finance")

    # Google News RSS — headlines
    news_events = fetch_news_events(stock_id, max_items=5)
    print(f"   📰 {len(news_events)} news events from RSS")

    all_raw = price_events + news_events

    for raw in all_raw:
        # Convert ISO timestamp strings to datetime
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            try:
                raw["timestamp"] = datetime.fromisoformat(ts)
            except ValueError:
                raw["timestamp"] = datetime.now(timezone.utc)

        tagged = tag_event(raw)
        event = Event(**tagged)
        db.add(event)
        db.flush()

        # Score against all theses for this stock
        theses = (
            db.query(Thesis)
            .join(WatchlistItem)
            .filter(WatchlistItem.stock_id == event.stock_id)
            .all()
        )
        for t in theses:
            rel = calculate_relevance(event, t)
            db.add(
                RelevanceScore(
                    event_id=event.id,
                    thesis_id=t.id,
                    score=rel["score"],
                    confidence=rel["confidence"],
                    reason=rel["reason"],
                )
            )

        total_events += 1

db.commit()
print(f"\n✅ Seed completed — {total_events} live events ingested & scored")
db.close()