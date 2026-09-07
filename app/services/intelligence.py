from dataclasses import dataclass
from typing import List, Optional, Dict, Literal


Momentum = Literal["Strong", "Neutral", "Weak"]

SignalKind = Literal[
    "unusual_volume",
    "discount_to_high",
    "near_high",
    "strong_momentum",
    "weak_momentum",
    "near_support",
    "volatility",
    "accumulation",
    "breakout",
]


@dataclass
class Quote:
    symbol: str
    yahoo: str
    name: str
    price: float
    prevClose: float
    changePct: float
    high52: float
    low52: float
    volume: float
    avgVolume: float
    volumeRatio: float
    sma20: float
    sma50: float
    ret5d: float
    atr14: float
    avgRange20: float
    range5: float
    spark: List[float]
    currency: str


@dataclass
class Signal:
    kind: SignalKind
    label: str
    detail: str
    weight: int


@dataclass
class Analysis:
    quote: Quote
    distHighPct: float
    distLowPct: float
    volumeDeltaPct: float
    momentum: Momentum
    signals: List[Signal]
    headline: str
    score: int
    suggestedTrigger: float
    triggerDirection: Literal["below", "above"]
    smartAction: str


def format_inr(value: float) -> str:
    return f"₹{value:,.2f}"


def format_pct(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}%"


def round_to_nice(value: float) -> float:
    if value >= 5000:
        return round(value / 50) * 50

    if value >= 1000:
        return round(value / 5) * 5

    if value >= 200:
        return round(value / 2) * 2

    return round(value * 10) / 10


def analyze_quote(
    quote: Quote,
    accumulation_zone: Optional[float] = None
) -> Analysis:

    # --------------------------------
    # BASIC CALCULATIONS
    # --------------------------------

    dist_high_pct = (
        (quote.price - quote.high52) / quote.high52
    ) * 100

    dist_low_pct = (
        (quote.price - quote.low52) / quote.low52
    ) * 100

    if quote.avgVolume > 0:
        volume_delta_pct = (
            (quote.volume - quote.avgVolume)
            / quote.avgVolume
        ) * 100
    else:
        volume_delta_pct = 0

    # --------------------------------
    # MOMENTUM
    # --------------------------------

    momentum: Momentum = "Neutral"

    if (
        quote.ret5d >= 3
        and quote.price >= quote.sma20
        and dist_high_pct > -12
    ):
        momentum = "Strong"

    elif (
        dist_high_pct <= -15
        or quote.ret5d < 0
        or quote.price < quote.sma20
    ):
        momentum = "Weak"

    # --------------------------------
    # SIGNALS
    # --------------------------------

    signals: List[Signal] = []

    # Unusual volume
    if volume_delta_pct >= 20:
        signals.append(
            Signal(
                kind="unusual_volume",
                label="Unusual volume",
                detail=(
                    f"Volume {format_pct(volume_delta_pct, 0)} "
                    f"vs 20-day average"
                ),
                weight=28
            )
        )

    # Distance from 52-week high
    if dist_high_pct <= -12:

        drop = abs(round(dist_high_pct))

        signals.append(
            Signal(
                kind="discount_to_high",
                label=f"↓ {drop}% from 52W high",
                detail=(
                    f"Last close is {drop}% below "
                    f"{format_inr(quote.high52)}"
                ),
                weight=18 if dist_high_pct <= -20 else 14
            )
        )

    elif dist_high_pct >= -3:

        signals.append(
            Signal(
                kind="near_high",
                label="Pressing 52W high",
                detail=(
                    f"{abs(dist_high_pct):.1f}% off the year high"
                ),
                weight=16
            )
        )

    # Momentum signal
    if momentum == "Strong":

        signals.append(
            Signal(
                kind="strong_momentum",
                label="Strong momentum",
                detail=f"↑ {quote.ret5d:.1f}% in 5D",
                weight=18
            )
        )

    elif momentum == "Weak":

        signals.append(
            Signal(
                kind="weak_momentum",
                label="Momentum: Weak",
                detail=(
                    f"5-day move {format_pct(quote.ret5d)} "
                    f"· below trend"
                ),
                weight=6
            )
        )

    # --------------------------------
    # SUPPORT
    # --------------------------------

    near_year_low = dist_low_pct <= 4

    near_sma50 = (
        quote.sma50 > 0
        and abs(quote.price - quote.sma50) / quote.sma50 <= 0.02
    )

    if (
        near_year_low
        or (near_sma50 and quote.price <= quote.sma20)
    ):

        if near_year_low:
            detail = (
                f"{dist_low_pct:.1f}% above the 52-week low"
            )
        else:
            detail = (
                f"Holding the 50-day average at "
                f"{format_inr(quote.sma50)}"
            )

        signals.append(
            Signal(
                kind="near_support",
                label="Price near support",
                detail=detail,
                weight=16
            )
        )

    # --------------------------------
    # VOLATILITY
    # --------------------------------

    if (
        quote.avgRange20 > 0
        and quote.range5 > quote.avgRange20 * 1.25
    ):

        signals.append(
            Signal(
                kind="volatility",
                label="Increasing volatility",
                detail=(
                    "5-day range is running hotter "
                    "than the 20-day norm"
                ),
                weight=10
            )
        )

    # --------------------------------
    # ACCUMULATION ZONE
    # --------------------------------

    if accumulation_zone and accumulation_zone > 0:

        dist_zone = (
            (quote.price - accumulation_zone)
            / accumulation_zone
        ) * 100

        if 0 <= dist_zone <= 8:

            signals.append(
                Signal(
                    kind="accumulation",
                    label="Near accumulation zone",
                    detail=(
                        f"Zone marked at "
                        f"{format_inr(accumulation_zone)}"
                    ),
                    weight=22
                )
            )

    # --------------------------------
    # BREAKOUT
    # --------------------------------

    if (
        quote.price > quote.sma20
        and quote.ret5d >= 2
        and volume_delta_pct >= 10
        and dist_high_pct > -8
    ):

        signals.append(
            Signal(
                kind="breakout",
                label="Volume-backed push",
                detail="Price and volume expanding together",
                weight=14
            )
        )

    # --------------------------------
    # REMOVE DUPLICATE SIGNAL TYPES
    # --------------------------------

    unique: Dict[SignalKind, Signal] = {}

    for signal in signals:

        previous = unique.get(signal.kind)

        if previous is None or signal.weight > previous.weight:
            unique[signal.kind] = signal

    # Sort by weight descending
    ranked = sorted(
        unique.values(),
        key=lambda s: s.weight,
        reverse=True
    )

    # --------------------------------
    # SCORE
    # --------------------------------

    score = sum(
        signal.weight
        for signal in ranked
    )

    # --------------------------------
    # HEADLINE
    # --------------------------------

    drop_abs = abs(round(dist_high_pct))

    vol = next(
        (s for s in ranked if s.kind == "unusual_volume"),
        None
    )

    disc = next(
        (s for s in ranked if s.kind == "discount_to_high"),
        None
    )

    sup = next(
        (s for s in ranked if s.kind == "near_support"),
        None
    )

    vola = next(
        (s for s in ranked if s.kind == "volatility"),
        None
    )

    acc = next(
        (s for s in ranked if s.kind == "accumulation"),
        None
    )

    strong = next(
        (s for s in ranked if s.kind == "strong_momentum"),
        None
    )

    if vol and disc:

        headline = (
            f"{quote.symbol} is showing unusual volume "
            f"while trading {drop_abs}% below its 52-week high."
        )

    elif acc:

        headline = (
            f"{quote.symbol} is approaching "
            f"your accumulation zone."
        )

    elif sup and vola:

        headline = (
            f"{quote.symbol} is sitting near support "
            f"with increasing volatility."
        )

    elif strong:

        headline = (
            f"{quote.symbol} is printing strong momentum, "
            f"up {quote.ret5d:.1f}% over 5 days."
        )

    elif vol:

        headline = (
            f"{quote.symbol} is seeing unusual volume "
            f"versus its 20-day average."
        )

    elif disc:

        headline = (
            f"{quote.symbol} is trading "
            f"{drop_abs}% below its 52-week high."
        )

    elif sup:

        headline = (
            f"{quote.symbol} is holding near support."
        )

    else:

        headline = (
            f"{quote.symbol} is quiet on the tape — "
            f"watching for a volume expansion."
        )

    # --------------------------------
    # SMART TRIGGER
    # --------------------------------

    trigger_direction: Literal["below", "above"] = "below"

    if accumulation_zone:

        suggested_trigger = round_to_nice(
            accumulation_zone
        )

        trigger_direction = "below"

        smart_action = (
            "Approaching your accumulation zone"
        )

    elif disc and vol:

        suggested_trigger = round_to_nice(
            quote.price * 0.968
        )

        trigger_direction = "below"

        smart_action = (
            "Approaching your accumulation zone"
        )

    elif sup:

        suggested_trigger = round_to_nice(
            max(
                quote.low52 * 1.002,
                quote.price * 0.985
            )
        )

        trigger_direction = "below"

        smart_action = (
            "Price is testing a support pocket"
        )

    elif (
        strong
        or any(s.kind == "near_high" for s in ranked)
    ):

        suggested_trigger = round_to_nice(
            quote.high52 * 0.997
        )

        trigger_direction = "above"

        smart_action = (
            "Breakout watch above the year high"
        )

    else:

        suggested_trigger = round_to_nice(
            quote.price * 0.98
        )

        trigger_direction = "below"

        smart_action = (
            "Set a dip-buy condition under last close"
        )

    # --------------------------------
    # RETURN
    # --------------------------------

    return Analysis(
        quote=quote,
        distHighPct=dist_high_pct,
        distLowPct=dist_low_pct,
        volumeDeltaPct=volume_delta_pct,
        momentum=momentum,
        signals=ranked,
        headline=headline,
        score=score,
        suggestedTrigger=suggested_trigger,
        triggerDirection=trigger_direction,
        smartAction=smart_action
    )


def rank_watchlist(
    quotes: List[Quote],
    zones: Dict[str, float]
) -> List[Analysis]:

    analyses = [
        analyze_quote(
            quote,
            zones.get(quote.symbol)
        )
        for quote in quotes
    ]

    return sorted(
        analyses,
        key=lambda a: (
            -a.score,
            abs(a.distHighPct)
        )
    )