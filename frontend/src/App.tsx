import { useState } from "react";
import { AppHeader } from "@/lib/components/smart/header";
import { AddBar } from "@/lib/components/smart/add-bar";
import { StockCard } from "@/lib/components/smart/stock-card";
import { StockDetailView } from "@/lib/components/smart/stock-detail";
import { AlertsRail } from "@/lib/components/smart/alerts-rail";
import { Button } from "@/lib/components/ui/button";
import { Skeleton } from "@/lib/components/ui/skeleton";
import { useMarket } from "@/lib/use-market";

export default function App() {
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  const {
    ranked,
    index,
    bySymbol,
    isPending,
    isError,
    refetch,
    isFetching,
    errorMessage,
  } = useMarket();

  const selectedQuote = selectedSymbol ? bySymbol.get(selectedSymbol) : null;

  return (
    <div className="min-h-dvh bg-bg text-fg font-sans antialiased selection:bg-primary/20">
      {selectedSymbol && selectedQuote ? (
        <StockDetailView
          quote={selectedQuote}
          onBack={() => setSelectedSymbol(null)}
        />
      ) : (
        <main className="mx-auto min-h-dvh w-full max-w-xl px-4 pt-6 pb-16">
          <AppHeader
            index={index}
            onSelectSymbol={(sym) => setSelectedSymbol(sym)}
          />

          <div className="mt-6">
            <AddBar onSelectSymbol={(sym) => setSelectedSymbol(sym)} />
          </div>

          <div className="mt-8 mb-3 flex items-center justify-between">
            <p className="text-[11px] font-medium tracking-[0.16em] text-muted uppercase">
              Today’s watchlist
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => void refetch()}
              disabled={isFetching}
            >
              <svg
                className={`size-3.5 ${isFetching ? "animate-spin" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Scan
            </Button>
          </div>

          {isPending && ranked.length === 0 ? (
            <div className="grid gap-3">
              <Skeleton className="h-52 rounded-xl" />
              <Skeleton className="h-40 rounded-xl" />
              <Skeleton className="h-40 rounded-xl" />
            </div>
          ) : isError && ranked.length === 0 ? (
            <div className="rounded-xl bg-surface p-6 text-center shadow-[var(--shadow-border)] border border-border/40">
              <p className="text-sm text-muted">
                Couldn’t load live quotes. Try scanning again.
              </p>
              {errorMessage ? (
                <p className="mt-2 font-mono text-xs text-faint">
                  {errorMessage}
                </p>
              ) : null}
              <Button className="mt-4" onClick={() => void refetch()}>
                Retry
              </Button>
            </div>
          ) : ranked.length === 0 ? (
            <div className="rounded-xl bg-surface p-8 text-center shadow-[var(--shadow-border)] border border-border/40">
              <p className="text-sm text-muted">
                Nothing on the radar yet. Add a ticker — the intelligence layer
                ranks what actually matters today.
              </p>
            </div>
          ) : (
            <div className="grid gap-3">
              {ranked.map((item, i) => (
                <StockCard
                  key={item.quote.symbol}
                  analysis={item}
                  rank={i + 1}
                  featured={i === 0}
                  onClick={() => setSelectedSymbol(item.quote.symbol)}
                />
              ))}
            </div>
          )}

          <AlertsRail onSelectSymbol={(sym) => setSelectedSymbol(sym)} />
        </main>
      )}
    </div>
  );
}
