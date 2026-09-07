import { formatInr, formatPct } from "../format";

export type Quote = {
  symbol: string;
  yahoo: string;
  name: string;
  price: number;
  prevClose: number;
  changePct: number;
  high52: number;
  low52: number;
  volume: number;
  avgVolume: number;
  sma20: number;
  sma50: number;
  ret5d: number;
  atr14: number;
  avgRange20: number;
  range5: number;
  spark: number[];
  currency: string;
};

export type Momentum = "Strong" | "Neutral" | "Weak";

export type SignalKind =
  | "unusual_volume"
  | "discount_to_high"
  | "near_high"
  | "strong_momentum"
  | "weak_momentum"
  | "near_support"
  | "volatility"
  | "accumulation"
  | "breakout";

export type Signal = {
  kind: SignalKind;
  label: string;
  detail: string;
  weight: number;
};

export type Analysis = {
  quote: Quote;
  distHighPct: number;
  distLowPct: number;
  volumeDeltaPct: number;
  momentum: Momentum;
  signals: Signal[];
  headline: string;
  score: number;
  suggestedTrigger: number;
  triggerDirection: "below" | "above";
  smartAction: string;
};

function roundToNice(value: number) {
  if (value >= 5000) return Math.round(value / 50) * 50;
  if (value >= 1000) return Math.round(value / 5) * 5;
  if (value >= 200) return Math.round(value / 2) * 2;
  return Math.round(value * 10) / 10;
}

export function analyzeQuote(quote: Quote, accumulationZone?: number): Analysis {
  const distHighPct = ((quote.price - quote.high52) / quote.high52) * 100;
  const distLowPct = ((quote.price - quote.low52) / quote.low52) * 100;
  const volumeDeltaPct =
    quote.avgVolume > 0 ? ((quote.volume - quote.avgVolume) / quote.avgVolume) * 100 : 0;

  let momentum: Momentum = "Neutral";
  if (quote.ret5d >= 3 && quote.price >= quote.sma20 && distHighPct > -12) {
    momentum = "Strong";
  } else if (distHighPct <= -15 || quote.ret5d < 0 || quote.price < quote.sma20) {
    momentum = "Weak";
  }

  const signals: Signal[] = [];

  if (volumeDeltaPct >= 20) {
    signals.push({
      kind: "unusual_volume",
      label: "Unusual volume",
      detail: `Volume ${formatPct(volumeDeltaPct, 0)} vs 20-day average`,
      weight: 28,
    });
  }

  if (distHighPct <= -12) {
    const drop = Math.abs(Math.round(distHighPct));
    signals.push({
      kind: "discount_to_high",
      label: `↓ ${drop}% from 52W high`,
      detail: `Last close is ${drop}% below ${formatInr(quote.high52)}`,
      weight: distHighPct <= -20 ? 18 : 14,
    });
  } else if (distHighPct >= -3) {
    signals.push({
      kind: "near_high",
      label: "Pressing 52W high",
      detail: `${Math.abs(distHighPct).toFixed(1)}% off the year high`,
      weight: 16,
    });
  }

  if (momentum === "Strong") {
    signals.push({
      kind: "strong_momentum",
      label: "Strong momentum",
      detail: `↑ ${quote.ret5d.toFixed(1)}% in 5D`,
      weight: 18,
    });
  } else if (momentum === "Weak") {
    signals.push({
      kind: "weak_momentum",
      label: "Momentum: Weak",
      detail: `5-day move ${formatPct(quote.ret5d)} · below trend`,
      weight: 6,
    });
  }

  const nearYearLow = distLowPct <= 4;
  const nearSma50 =
    quote.sma50 > 0 && Math.abs(quote.price - quote.sma50) / quote.sma50 <= 0.02;
  if (nearYearLow || (nearSma50 && quote.price <= quote.sma20)) {
    signals.push({
      kind: "near_support",
      label: "Price near support",
      detail: nearYearLow
        ? `${distLowPct.toFixed(1)}% above the 52-week low`
        : `Holding the 50-day average at ${formatInr(quote.sma50)}`,
      weight: 16,
    });
  }

  if (quote.avgRange20 > 0 && quote.range5 > quote.avgRange20 * 1.25) {
    signals.push({
      kind: "volatility",
      label: "Increasing volatility",
      detail: "5-day range is running hotter than the 20-day norm",
      weight: 10,
    });
  }

  if (accumulationZone && accumulationZone > 0) {
    const distZone = ((quote.price - accumulationZone) / accumulationZone) * 100;
    if (distZone >= 0 && distZone <= 8) {
      signals.push({
        kind: "accumulation",
        label: "Near accumulation zone",
        detail: `Zone marked at ${formatInr(accumulationZone)}`,
        weight: 22,
      });
    }
  }

  if (quote.price > quote.sma20 && quote.ret5d >= 2 && volumeDeltaPct >= 10 && distHighPct > -8) {
    signals.push({
      kind: "breakout",
      label: "Volume-backed push",
      detail: "Price and volume expanding together",
      weight: 14,
    });
  }

  const unique = new Map<SignalKind, Signal>();
  for (const s of signals) {
    const prev = unique.get(s.kind);
    if (!prev || s.weight > prev.weight) unique.set(s.kind, s);
  }
  const ranked = [...unique.values()].sort((a, b) => b.weight - a.weight);
  const score = ranked.reduce((sum, s) => sum + s.weight, 0);

  const dropAbs = Math.abs(Math.round(distHighPct));
  let headline: string;
  const vol = ranked.find((s) => s.kind === "unusual_volume");
  const disc = ranked.find((s) => s.kind === "discount_to_high");
  const sup = ranked.find((s) => s.kind === "near_support");
  const vola = ranked.find((s) => s.kind === "volatility");
  const acc = ranked.find((s) => s.kind === "accumulation");
  const strong = ranked.find((s) => s.kind === "strong_momentum");

  if (vol && disc) {
    headline = `${quote.symbol} is showing unusual volume while trading ${dropAbs}% below its 52-week high.`;
  } else if (acc) {
    headline = `${quote.symbol} is approaching your accumulation zone.`;
  } else if (sup && vola) {
    headline = `${quote.symbol} is sitting near support with increasing volatility.`;
  } else if (strong) {
    headline = `${quote.symbol} is printing strong momentum, up ${quote.ret5d.toFixed(1)}% over 5 days.`;
  } else if (vol) {
    headline = `${quote.symbol} is seeing unusual volume versus its 20-day average.`;
  } else if (disc) {
    headline = `${quote.symbol} is trading ${dropAbs}% below its 52-week high.`;
  } else if (sup) {
    headline = `${quote.symbol} is holding near support.`;
  } else {
    headline = `${quote.symbol} is quiet on the tape — watching for a volume expansion.`;
  }

  let suggestedTrigger: number;
  let triggerDirection: "below" | "above" = "below";
  let smartAction: string;

  if (accumulationZone) {
    suggestedTrigger = roundToNice(accumulationZone);
    triggerDirection = "below";
    smartAction = "Approaching your accumulation zone";
  } else if (disc && vol) {
    suggestedTrigger = roundToNice(quote.price * 0.968);
    triggerDirection = "below";
    smartAction = "Approaching your accumulation zone";
  } else if (sup) {
    suggestedTrigger = roundToNice(Math.max(quote.low52 * 1.002, quote.price * 0.985));
    triggerDirection = "below";
    smartAction = "Price is testing a support pocket";
  } else if (strong || ranked.some((s) => s.kind === "near_high")) {
    suggestedTrigger = roundToNice(quote.high52 * 0.997);
    triggerDirection = "above";
    smartAction = "Breakout watch above the year high";
  } else {
    suggestedTrigger = roundToNice(quote.price * 0.98);
    triggerDirection = "below";
    smartAction = "Set a dip-buy condition under last close";
  }

  return {
    quote,
    distHighPct,
    distLowPct,
    volumeDeltaPct,
    momentum,
    signals: ranked,
    headline,
    score,
    suggestedTrigger,
    triggerDirection,
    smartAction,
  };
}

export function rankWatchlist(
  quotes: Quote[],
  zones: Record<string, number>,
): Analysis[] {
  return quotes
    .map((q) => analyzeQuote(q, zones[q.symbol]))
    .sort((a, b) => b.score - a.score || Math.abs(a.distHighPct) - Math.abs(b.distHighPct));
}
