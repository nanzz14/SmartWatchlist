import React from "react";
import { Badge } from "@/lib/components/ui/badge";
import { RangeTrack, Sparkline } from "@/lib/components/smart/sparkline";
import { formatInr, formatPct } from "@/lib/format";
import type { Analysis } from "@/lib/market/intelligence";
import { cn } from "@/lib/utils";

export function StockCard({
  analysis,
  rank,
  featured = false,
  onClick,
}: {
  analysis: Analysis;
  rank: number;
  featured?: boolean;
  onClick?: () => void;
}) {
  const { quote, signals, headline, distHighPct, volumeDeltaPct, momentum } = analysis;
  const up = quote.changePct >= 0;
  const reasons = signals
    .filter((s) => s.kind !== "weak_momentum" || featured)
    .slice(0, featured ? 3 : 3);

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.();
        }
      }}
      className={cn(
        "stagger-in block rounded-xl bg-surface p-4 shadow-[var(--shadow-border)] transition-[box-shadow,transform] duration-150 cursor-pointer border border-border/40 hover:border-border/80",
        "hover:shadow-[var(--shadow-border-hover)] hover:-translate-y-0.5",
        featured && "p-5 border-primary/30",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-faint tabular-nums">#{rank}</span>
            <h2 className={cn("font-semibold tracking-tight text-fg", featured ? "text-xl" : "text-base")}>
              {quote.symbol}
            </h2>
            {signals.some((s) => s.kind === "unusual_volume") ? (
              <span title="Unusual Volume" className="text-warn text-xs">⚡</span>
            ) : null}
          </div>
          <p className="mt-0.5 truncate text-sm text-muted">{quote.name}</p>
        </div>
        <div className="text-right">
          <p className="font-mono text-base tabular-nums font-medium text-fg">{formatInr(quote.price)}</p>
          <p className={cn("font-mono text-xs tabular-nums font-semibold", up ? "text-up" : "text-down")}>
            {formatPct(quote.changePct)}
          </p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {reasons.map((r) => (
          <Badge
            key={r.kind}
            variant={
              r.kind === "unusual_volume" || r.kind === "volatility"
                ? "warn"
                : r.kind === "strong_momentum"
                  ? "live"
                  : "default"
            }
          >
            {r.label}
          </Badge>
        ))}
      </div>

      {featured ? (
        <div className="mt-4 flex gap-3 rounded-lg bg-elevated p-3 border border-border/40">
          <span className="mt-0.5 text-warn text-sm shrink-0">⚠️</span>
          <p className="text-sm leading-relaxed text-fg">{headline}</p>
        </div>
      ) : null}

      <div className="mt-4 grid grid-cols-[1fr_88px] items-end gap-4">
        <div>
          <div className="mb-2 flex justify-between font-mono text-[11px] text-faint tabular-nums">
            <span>{formatInr(quote.low52, { compact: true })}</span>
            <span>{formatInr(quote.high52, { compact: true })}</span>
          </div>
          <RangeTrack low={quote.low52} high={quote.high52} value={quote.price} />
          <p className="mt-2 text-[11px] text-muted">
            {distHighPct < 0
              ? `${Math.abs(Math.round(distHighPct))}% below 52W high`
              : "At 52W high"}
            {volumeDeltaPct >= 8 ? ` · vol ${formatPct(volumeDeltaPct, 0)}` : ""}
            {` · ${momentum}`}
          </p>
        </div>
        <Sparkline
          data={quote.spark}
          tone={up ? "up" : "down"}
          className="h-9 w-[88px]"
        />
      </div>
    </div>
  );
}
