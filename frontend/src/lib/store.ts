import { useState, useEffect } from "react";
import { DEFAULT_WATCHLIST } from "@/lib/market/universe";

export type WatchAlert = {
  id: string;
  symbol: string;
  trigger: number;
  direction: "below" | "above";
  note: string;
  createdAt: number;
  firedAt: number | null;
};

export type WatchData = {
  watchlist: string[];
  thesis: Record<string, string>;
  zones: Record<string, number>;
  alerts: WatchAlert[];
};

export type WatchState = WatchData & {
  hydrated: boolean;
  setHydrated: (v: boolean) => void;
  addSymbol: (symbol: string, thesis?: string) => void;
  removeSymbol: (symbol: string) => void;
  setThesis: (symbol: string, text: string) => void;
  setZone: (symbol: string, price: number) => void;
  addAlert: (input: Omit<WatchAlert, "id" | "createdAt" | "firedAt">) => WatchAlert;
  removeAlert: (id: string) => void;
  markFired: (id: string) => void;
};

const STORAGE_KEY = "smartwatchlist.v1";

function loadInitialData(): WatchData {
  if (typeof window === "undefined") {
    return { watchlist: DEFAULT_WATCHLIST, thesis: {}, zones: {}, alerts: [] };
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        watchlist: Array.isArray(parsed?.state?.watchlist)
          ? parsed.state.watchlist
          : Array.isArray(parsed?.watchlist)
          ? parsed.watchlist
          : DEFAULT_WATCHLIST,
        thesis: parsed?.state?.thesis ?? parsed?.thesis ?? {},
        zones: parsed?.state?.zones ?? parsed?.zones ?? {},
        alerts: parsed?.state?.alerts ?? parsed?.alerts ?? [],
      };
    }
  } catch (err) {
    console.error("Failed to parse watchlist storage", err);
  }
  return { watchlist: DEFAULT_WATCHLIST, thesis: {}, zones: {}, alerts: [] };
}

let currentState: WatchData = loadInitialData();
const listeners = new Set<() => void>();

function saveState() {
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ state: currentState }));
    } catch (e) {
      console.error("Failed to save watchlist storage", e);
    }
  }
  listeners.forEach((listener) => listener());
}

export const watchStoreActions = {
  getState: (): WatchState => ({
    ...currentState,
    hydrated: true,
    setHydrated: () => {},
    addSymbol: watchStoreActions.addSymbol,
    removeSymbol: watchStoreActions.removeSymbol,
    setThesis: watchStoreActions.setThesis,
    setZone: watchStoreActions.setZone,
    addAlert: watchStoreActions.addAlert,
    removeAlert: watchStoreActions.removeAlert,
    markFired: watchStoreActions.markFired,
  }),
  addSymbol: (symbol: string, thesisText?: string) => {
    const next = symbol.toUpperCase().trim();
    if (!next) return;
    const exists = currentState.watchlist.includes(next);
    currentState = {
      ...currentState,
      watchlist: exists ? currentState.watchlist : [next, ...currentState.watchlist],
      thesis: thesisText
        ? { ...currentState.thesis, [next]: thesisText }
        : currentState.thesis,
    };
    saveState();
  },
  removeSymbol: (symbol: string) => {
    const next = symbol.toUpperCase().trim();
    const { [next]: _t, ...thesis } = currentState.thesis;
    const { [next]: _z, ...zones } = currentState.zones;
    currentState = {
      ...currentState,
      watchlist: currentState.watchlist.filter((s) => s !== next),
      thesis,
      zones,
      alerts: currentState.alerts.filter((a) => a.symbol !== next),
    };
    saveState();
  },
  setThesis: (symbol: string, text: string) => {
    currentState = {
      ...currentState,
      thesis: { ...currentState.thesis, [symbol.toUpperCase()]: text },
    };
    saveState();
  },
  setZone: (symbol: string, price: number) => {
    currentState = {
      ...currentState,
      zones: { ...currentState.zones, [symbol.toUpperCase()]: price },
    };
    saveState();
  },
  addAlert: (input: Omit<WatchAlert, "id" | "createdAt" | "firedAt">): WatchAlert => {
    const alert: WatchAlert = {
      ...input,
      symbol: input.symbol.toUpperCase(),
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      createdAt: Date.now(),
      firedAt: null,
    };
    currentState = {
      ...currentState,
      alerts: [alert, ...currentState.alerts],
    };
    saveState();
    return alert;
  },
  removeAlert: (id: string) => {
    currentState = {
      ...currentState,
      alerts: currentState.alerts.filter((a) => a.id !== id),
    };
    saveState();
  },
  markFired: (id: string) => {
    currentState = {
      ...currentState,
      alerts: currentState.alerts.map((a) =>
        a.id === id && !a.firedAt ? { ...a, firedAt: Date.now() } : a,
      ),
    };
    saveState();
  },
};

export function useWatchStore<T = WatchState>(selector?: (state: WatchState) => T): T {
  const [snap, setSnap] = useState(() => watchStoreActions.getState());

  useEffect(() => {
    const handleChange = () => setSnap(watchStoreActions.getState());
    listeners.add(handleChange);
    return () => {
      listeners.delete(handleChange);
    };
  }, []);

  if (selector) {
    return selector(snap);
  }
  return snap as unknown as T;
}

// Attach static helpers for compatibility with zustand patterns
(useWatchStore as any).getState = watchStoreActions.getState;
(useWatchStore as any).persist = {
  rehydrate: () => {
    currentState = loadInitialData();
    saveState();
  },
};
