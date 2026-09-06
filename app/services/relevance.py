"""
Rule-based relevance scoring engine.

Compares an Event against a Thesis to determine how relevant the event
is to the user's investment thesis.  No LLM required — uses tag overlap,
keyword matching in free-text, and magnitude weighting.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.config import settings


# ── helpers ──────────────────────────────────────────────────────────────

def _tag_overlap_score(event_tags: List[str], thesis_tags: List[str]) -> float:
    """Jaccard-like overlap between event tags and thesis tags (0-1)."""
    if not event_tags or not thesis_tags:
        return 0.0
    event_set = {t.lower() for t in event_tags}
    thesis_set = {t.lower() for t in thesis_tags}
    intersection = event_set & thesis_set
    union = event_set | thesis_set
    return len(intersection) / len(union) if union else 0.0


def _keyword_score(thesis_text: str | None, payload: dict) -> float:
    """
    Simple keyword match: split thesis free-text into words and check
    how many appear in the event payload (headline, keys, values).
    Returns 0-1.
    """
    if not thesis_text:
        return 0.0

    # Flatten payload into a single searchable string
    payload_blob = " ".join(
        str(v) for v in _flatten_values(payload)
    ).lower()

    words = [w.lower() for w in thesis_text.split() if len(w) > 3]  # skip tiny words
    if not words:
        return 0.0

    hits = sum(1 for w in words if w in payload_blob)
    return hits / len(words)


def _flatten_values(d: dict) -> list:
    """Recursively extract all string/number values from a dict."""
    out: list = []
    for v in d.values():
        if isinstance(v, dict):
            out.extend(_flatten_values(v))
        elif isinstance(v, list):
            out.extend(str(item) for item in v)
        else:
            out.append(str(v))
    return out


def _magnitude_multiplier(magnitude: float) -> float:
    """Scale score upward for high-magnitude events (diminishing returns)."""
    if magnitude <= 0:
        return 0.5
    if magnitude < 1:
        return 0.7
    if magnitude < 3:
        return 1.0
    if magnitude < 5:
        return 1.15
    return 1.3  # very large event


# ── public API ───────────────────────────────────────────────────────────

def calculate_relevance(event, thesis) -> Dict[str, Any]:
    """
    Score how relevant *event* is to *thesis*.

    Parameters
    ----------
    event : app.models.Event  (or any object with .type, .payload, .magnitude)
    thesis : app.models.Thesis (or any object with .tags, .free_text)

    Returns
    -------
    dict  {"score": float, "confidence": float, "reason": str}
        score      – 0.0 … 1.0  (higher = more relevant)
        confidence – 0.0 … 1.0  (how sure we are about the score)
        reason     – human-readable explanation
    """
    payload = event.payload or {}
    event_tags: List[str] = payload.get("tags", [])
    thesis_tags: List[str] = thesis.tags or []

    # 1. Tag overlap  (weight: 50 %)
    tag_score = _tag_overlap_score(event_tags, thesis_tags)

    # 2. Keyword match (weight: 30 %)
    kw_score = _keyword_score(thesis.free_text, payload)

    # 3. Magnitude boost (multiplier)
    mag_mult = _magnitude_multiplier(event.magnitude or 0.0)

    # Weighted blend
    raw = (0.50 * tag_score + 0.30 * kw_score + 0.20 * min(mag_mult, 1.0))
    # Apply magnitude multiplier on top
    score = min(raw * mag_mult, 1.0)
    score = round(score, 4)

    # Confidence: higher when we have more signal
    signals = sum([
        tag_score > 0,
        kw_score > 0,
        (event.magnitude or 0) > 1,
        len(event_tags) >= 2,
    ])
    confidence = round(min(0.3 + signals * 0.175, 1.0), 4)

    # Build reason
    parts: list[str] = []
    if tag_score > 0:
        overlap_tags = set(t.lower() for t in event_tags) & set(t.lower() for t in thesis_tags)
        parts.append(f"Tag overlap on [{', '.join(sorted(overlap_tags))}] ({tag_score:.0%})")
    if kw_score > 0:
        parts.append(f"Keyword match in thesis text ({kw_score:.0%})")
    if (event.magnitude or 0) > 1:
        parts.append(f"High magnitude event ({event.magnitude:.1f})")
    if not parts:
        parts.append("No strong signal between event and thesis")

    reason = "; ".join(parts)

    return {"score": score, "confidence": confidence, "reason": reason}
