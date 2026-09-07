import React from "react";
import { formatIstClock, formatPct, isNseSession } from "@/lib/format";
import type { Quote } from "@/lib/market/intelligence";
import { Badge } from "@/lib/components/ui/badge";
import { cn } from "@/lib/utils";

export function AppHeader({
  index,
  onSelectSymbol,
}: {
  index: Quote | null;
  onSelectSymbol?: (symbol: string | null) => void;
}) {
  const open = isNseSession();
  return (
    <header className="flex items-start justify-between gap-4">
      <div>
        <button
          type="button"
          onClick={() => onSelectSymbol?.(null)}
          className="block text-left cursor-pointer group"
        >
          <p className="text-[11px] font-medium tracking-[0.18em] text-muted uppercase group-hover:text-primary transition-colors">
            SmartWatchlist
          </p>
          <h1 className="mt-1 text-[26px] leading-tight font-semibold tracking-tight">
            What should I watch today?
          </h1>
        </button>
        <p className="mt-1.5 text-sm text-muted">{formatIstClock()}</p>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-2">
        <Badge variant={open ? "live" : "outline"} className="h-7 gap-2 px-2.5">
          {open ? <span className="live-dot" /> : <span className="size-1.5 rounded-full bg-faint" />}
          {open ? "LIVE" : "NSE closed"}
        </Badge>
        {index ? (
          <div className="text-right">
            <p className="text-[11px] tracking-wide text-faint uppercase">Nifty 50</p>
            <p className="font-mono text-sm tabular-nums">
              {index.price.toLocaleString("en-IN", { maximumFractionDigits: 1 })}
              <span
                className={cn("ml-1.5", index.changePct >= 0 ? "text-up" : "text-down")}
              >
                {formatPct(index.changePct)}
              </span>
            </p>
          </div>
        ) : null}
      </div>
    </header>
  );
}
