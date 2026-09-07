import { useState } from "react";
import { Badge } from "@/lib/components/ui/badge";
import { Button } from "@/lib/components/ui/button";
import { RangeTrack, Sparkline } from "@/lib/components/smart/sparkline";
import { SetAlertDialog } from "@/lib/components/smart/set-alert";
import { formatCompact, formatInr, formatPct } from "@/lib/format";
import { analyzeQuote, type Quote } from "@/lib/market/intelligence";
import { useWatchStore } from "@/lib/store";
import { cn } from "@/lib/utils";

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-md bg-elevated px-3 py-3 border border-border/30">
      <p className="text-[11px] tracking-wide text-faint uppercase">{label}</p>
      <p className="mt-1 font-mono text-sm tabular-nums font-semibold text-fg">{value}</p>
      {hint ? <p className="mt-0.5 text-[11px] text-muted">{hint}</p> : null}
    </div>
  );
}

export function StockDetailView({
  quote,
  onBack,
}: {
  quote: Quote;
  onBack?: () => void;
}) {
  const zones = useWatchStore((s) => s.zones);
  const alerts = useWatchStore((s) => s.alerts);
  const removeSymbol = useWatchStore((s) => s.removeSymbol);
  const removeAlert = useWatchStore((s) => s.removeAlert);

  const analysis = analyzeQuote(quote, zones[quote.symbol]);
  const [open, setOpen] = useState(false);
  const up = quote.changePct >= 0;
  const mine = alerts.filter((a) => a.symbol === quote.symbol);
  const volAbs = Math.abs(Math.round(analysis.volumeDeltaPct));

  return (
    <div className="mx-auto max-w-xl px-4 pt-6 pb-16">
      <div className="mb-6 flex items-center justify-between">
        <Button variant="outline" size="sm" onClick={onBack} aria-label="Back to watchlist">
          <svg className="size-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back
        </Button>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Remove from watchlist"
          onClick={() => {
            removeSymbol(quote.symbol);
            onBack?.();
          }}
          className="text-down hover:text-down hover:bg-down/10"
        >
          <svg className="size-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Remove
        </Button>
      </div>

      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-xs tracking-[0.14em] text-muted">{quote.symbol}</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-fg">{quote.name}</h1>
        </div>
        <div className="text-right">
          <p className="font-mono text-2xl tabular-nums font-bold text-fg">{formatInr(quote.price)}</p>
          <p className={cn("font-mono text-sm tabular-nums font-semibold", up ? "text-up" : "text-down")}>
            {formatPct(quote.changePct)}
          </p>
        </div>
      </div>

      <Sparkline data={quote.spark} tone={up ? "up" : "down"} className="mt-5 h-16 w-full" />
      <div className="mt-4">
        <div className="mb-2 flex justify-between font-mono text-[11px] text-faint tabular-nums">
          <span>52W {formatInr(quote.low52)}</span>
          <span>{formatInr(quote.high52)}</span>
        </div>
        <RangeTrack low={quote.low52} high={quote.high52} value={quote.price} />
      </div>

      <div className="mt-6 grid grid-cols-2 gap-2">
        <Stat
          label="Current"
          value={formatInr(quote.price)}
          hint={`Prev ${formatInr(quote.prevClose)}`}
        />
        <Stat
          label="52W high"
          value={formatInr(quote.high52)}
          hint={`${Math.abs(Math.round(analysis.distHighPct))}% away`}
        />
        <Stat label="Distance from high" value={formatPct(analysis.distHighPct, 0)} />
        <Stat label="Momentum" value={analysis.momentum} hint={`${formatPct(quote.ret5d)} in 5D`} />
        <Stat
          label="Volume"
          value={`${analysis.volumeDeltaPct >= 0 ? "+" : "-"}${volAbs}%`}
          hint={`${formatCompact(quote.volume)} vs ${formatCompact(quote.avgVolume)} avg`}
        />
        <Stat
          label="Support"
          value={formatInr(quote.low52)}
          hint={`${analysis.distLowPct.toFixed(1)}% above 52W low`}
        />
      </div>

      <section className="mt-6 rounded-xl bg-surface p-5 shadow-[var(--shadow-border)] border border-border/40">
        <p className="text-[11px] tracking-[0.16em] text-muted uppercase">Smart signal</p>
        <p className="mt-2 text-lg font-medium tracking-tight text-fg">{analysis.smartAction}</p>
        <p className="mt-2 text-sm leading-relaxed text-muted">{analysis.headline}</p>
        <div className="mt-4 flex flex-wrap gap-1.5">
          {analysis.signals.slice(0, 4).map((s) => (
            <Badge key={s.kind} variant={s.kind === "unusual_volume" ? "warn" : "default"}>
              {s.label}
            </Badge>
          ))}
        </div>
        <div className="mt-5 flex items-end justify-between gap-4">
          <div>
            <p className="text-[11px] tracking-wide text-faint uppercase">Suggested trigger</p>
            <p className="font-mono text-xl tabular-nums font-semibold text-fg">{formatInr(analysis.suggestedTrigger)}</p>
            <p className="text-xs text-muted">
              {analysis.triggerDirection === "below" ? "At or below" : "At or above"}
            </p>
          </div>
          <Button onClick={() => setOpen(true)}>
            <svg className="size-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            Set alert
          </Button>
        </div>
      </section>

      {mine.length ? (
        <section className="mt-6">
          <p className="mb-2 text-sm font-medium text-muted">Watch conditions</p>
          <ul className="grid gap-2">
            {mine.map((a) => (
              <li
                key={a.id}
                className="flex items-center justify-between rounded-lg bg-surface px-3.5 py-3 shadow-[var(--shadow-border)] border border-border/40"
              >
                <div>
                  <p className="font-mono text-sm tabular-nums font-semibold text-fg">{formatInr(a.trigger)}</p>
                  <p className="text-xs text-muted">
                    {a.direction === "below" ? "at or below" : "at or above"}
                    {a.firedAt ? " · triggered" : ""}
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => removeAlert(a.id)}>
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <SetAlertDialog
        key={`${quote.symbol}-${analysis.suggestedTrigger}`}
        open={open}
        onOpenChange={setOpen}
        analysis={analysis}
      />
    </div>
  );
}
