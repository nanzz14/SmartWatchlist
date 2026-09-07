import React from "react";
import { formatInr } from "@/lib/format";
import { useWatchStore } from "@/lib/store";
import { Badge } from "@/lib/components/ui/badge";

export function AlertsRail({ onSelectSymbol }: { onSelectSymbol?: (symbol: string) => void }) {
  const alerts = useWatchStore((s) => s.alerts);
  if (!alerts.length) return null;
  return (
    <section className="mt-8">
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-muted">
        <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        Active alerts
      </div>
      <ul className="grid gap-2">
        {alerts.map((a) => (
          <li key={a.id}>
            <div
              role="button"
              tabIndex={0}
              onClick={() => onSelectSymbol?.(a.symbol)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectSymbol?.(a.symbol);
                }
              }}
              className="flex items-center justify-between rounded-lg bg-surface px-3.5 py-3 shadow-[var(--shadow-border)] border border-border/40 cursor-pointer hover:bg-elevated transition-colors"
            >
              <div>
                <p className="font-mono text-sm font-semibold text-fg">{a.symbol}</p>
                <p className="text-xs text-muted">{a.note}</p>
              </div>
              <div className="text-right">
                <p className="font-mono text-sm tabular-nums font-medium text-fg">{formatInr(a.trigger)}</p>
                {a.firedAt ? (
                  <Badge variant="warn">Triggered</Badge>
                ) : (
                  <p className="text-[11px] text-faint">
                    {a.direction === "below" ? "at or below" : "at or above"}
                  </p>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
