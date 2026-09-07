import { useEffect, useState, useCallback, useMemo } from "react";
import {
  rankWatchlist,
  type Analysis,
  type Quote,
} from "./market/intelligence";
import { useWatchStore } from "./store";

export function useMarket(
  customWatchlist?: string[],
  customZones?: Record<string, number>,
  extraSymbols: string[] = []
) {
  const storeWatchlist = useWatchStore((s) => s.watchlist);
  const storeZones = useWatchStore((s) => s.zones);

  const watchlist = customWatchlist ?? storeWatchlist;
  const zones = customZones ?? storeZones;

  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [ranked, setRanked] = useState<Analysis[]>([]);
  const [index, setIndex] = useState<Quote | null>(null);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const symbols = useMemo(
    () => [...new Set([...watchlist, ...extraSymbols])],
    [watchlist.join(","), extraSymbols.join(",")]
  );

  const fetchMarket = useCallback(async () => {
    if (symbols.length === 0) {
      setQuotes([]);
      setRanked([]);
      return;
    }

    try {
      setLoading(true);
      setErrorMessage(null);

      // Try local dev server endpoint, with relative /api fallback
      let response: Response;
      try {
        response = await fetch("/api/market/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symbols, zones }),
        });
      } catch {
        response = await fetch("http://localhost:8000/api/market/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symbols, zones }),
        });
      }

      if (!response.ok) {
        throw new Error(`Market API returned HTTP ${response.status}`);
      }

      const data = await response.json();

      const fetchedQuotes: Quote[] = data.quotes ?? [];
      setQuotes(fetchedQuotes);

      const analyses = rankWatchlist(
        fetchedQuotes.filter((q) => watchlist.includes(q.symbol)),
        zones
      );

      setRanked(analyses);
      setIndex(data.index ?? null);
    } catch (error) {
      console.warn("Market fetch fallback triggered:", error);
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to fetch market data"
      );
    } finally {
      setLoading(false);
    }
  }, [symbols.join(","), watchlist.join(","), JSON.stringify(zones)]);

  useEffect(() => {
    fetchMarket();
  }, [fetchMarket]);

  useEffect(() => {
    const interval = setInterval(fetchMarket, 60_000);
    return () => clearInterval(interval);
  }, [fetchMarket]);

  const bySymbol = useMemo(
    () => new Map(quotes.map((quote) => [quote.symbol, quote])),
    [quotes]
  );

  return {
    quotes,
    ranked,
    bySymbol,
    index,

    loading,
    isPending: loading,
    isFetching: loading,
    errorMessage,
    isError: Boolean(errorMessage),

    live: true,

    refresh: fetchMarket,
    refetch: fetchMarket,
  };
}