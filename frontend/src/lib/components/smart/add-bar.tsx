import { useMemo, useState } from "react";
import { Button } from "@/lib/components/ui/button";
import { Input } from "@/lib/components/ui/input";
import { resolveTicker, searchUniverse } from "@/lib/market/universe";
import { useWatchStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export function AddBar({ onSelectSymbol }: { onSelectSymbol?: (symbol: string) => void }) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const addSymbol = useWatchStore((s) => s.addSymbol);
  const watchlist = useWatchStore((s) => s.watchlist);

  const suggestions = useMemo(() => searchUniverse(q, 6), [q]);

  async function add(raw: string) {
    const resolved = resolveTicker(raw);
    if (!resolved) {
      setMessage("Couldn’t resolve ticker");
      return;
    }
    setBusy(true);
    try {
      addSymbol(resolved.symbol);
      setMessage(`Added ${resolved.symbol}`);
      setQ("");
      setOpen(false);
      if (onSelectSymbol) {
        onSelectSymbol(resolved.symbol);
      }
      setTimeout(() => setMessage(null), 3000);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative">
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void add(q);
        }}
      >
        <div className="relative flex-1">
          <span className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-faint flex items-center justify-center">
            <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <Input
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onBlur={() => {
              window.setTimeout(() => setOpen(false), 120);
            }}
            placeholder="Add RELIANCE, TCS, HDFC…"
            className="pl-10"
            autoComplete="off"
            aria-label="Add ticker"
          />
        </div>
        <Button type="submit" disabled={busy || !q.trim()} className="px-4">
          <svg className="size-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add
        </Button>
      </form>

      {message ? (
        <div className="mt-2 text-xs text-primary font-medium">{message}</div>
      ) : null}

      {open && suggestions.length > 0 ? (
        <ul className="absolute z-20 mt-2 w-full overflow-hidden rounded-lg bg-surface p-1 shadow-[var(--shadow-border)] border border-border/40">
          {suggestions.map((s) => {
            const onList = watchlist.includes(s.symbol);
            return (
              <li key={s.symbol}>
                <button
                  type="button"
                  className={cn(
                    "flex h-11 w-full items-center justify-between rounded-md px-3 text-left hover:bg-elevated cursor-pointer"
                  )}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => void add(s.symbol)}
                >
                  <span>
                    <span className="font-mono text-sm font-semibold">{s.symbol}</span>
                    <span className="ml-2 text-sm text-muted">{s.name}</span>
                  </span>
                  <span className="text-[11px] text-faint">{onList ? "Watching" : "Add"}</span>
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
