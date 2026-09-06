from datetime import datetime
from typing import Dict, Any

def tag_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure function: takes raw market/news data and returns a tagged event.
    Completely independent of any user thesis.
    """
    stock_id = raw["stock_id"]
    source = raw.get("source", "manual")
    timestamp = raw.get("timestamp", datetime.utcnow())
    payload = raw.get("payload", {})

    event_type = "unknown"
    magnitude = 0.0
    tags = []

    # ----- Price + Volume -----
    if "pct_change" in payload:
        pct = abs(payload["pct_change"])
        volume_ratio = payload.get("volume_ratio", 1.0)

        if pct >= 5 and volume_ratio >= 1.5:
            event_type = "price_move_significant"
            magnitude = pct * volume_ratio
            tags = ["price_move", "high_volume"]
        elif pct >= 3:
            event_type = "price_move"
            magnitude = pct
            tags = ["price_move"]

    # ----- Earnings -----
    elif "eps_surprise_pct" in payload:
        surprise = payload["eps_surprise_pct"]
        margin_change = payload.get("margin_change_bps", 0)

        if surprise > 5:
            event_type = "earnings_beat"
            magnitude = surprise
            tags = ["earnings", "earnings_beat"]
            if margin_change > 50:
                tags.append("margin_expansion")
        elif surprise < -5:
            event_type = "earnings_miss"
            magnitude = abs(surprise)
            tags = ["earnings", "earnings_miss"]
            if margin_change < -50:
                tags.append("margin_contraction")

    # ----- Analyst Rating -----
    elif "rating_change" in payload:
        change = str(payload["rating_change"]).lower()
        if "upgrade" in change or "buy" in change:
            event_type = "rating_upgrade"
            tags = ["rating", "upgrade"]
        elif "downgrade" in change or "sell" in change:
            event_type = "rating_downgrade"
            tags = ["rating", "downgrade"]
        magnitude = 1.0

    # ----- News / Filings (simple keyword) -----
    elif "headline" in payload:
        headline = str(payload["headline"]).lower()
        if any(w in headline for w in ["promoter", "pledged", "sold shares"]):
            event_type = "promoter_action"
            tags = ["promoter", "ownership"]
            magnitude = 1.5
        elif any(w in headline for w in ["ceo", "cfo", "management change"]):
            event_type = "management_change"
            tags = ["management"]
            magnitude = 1.2
        elif any(w in headline for w in ["new product", "launch", "unveils"]):
            event_type = "product_launch"
            tags = ["product"]
            magnitude = 1.0
        else:
            event_type = "news"
            tags = ["news"]
            magnitude = 0.5

    return {
        "stock_id": stock_id,
        "source": source,
        "type": event_type,
        "payload": {**payload, "tags": tags},
        "magnitude": round(magnitude, 2),
        "timestamp": timestamp
    }