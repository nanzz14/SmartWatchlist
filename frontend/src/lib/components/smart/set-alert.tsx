import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/lib/components/ui/dialog";
import { Button } from "@/lib/components/ui/button";
import { Input } from "@/lib/components/ui/input";
import { Label } from "@/lib/components/ui/label";
import { formatInr } from "@/lib/format";
import type { Analysis } from "@/lib/market/intelligence";
import { useWatchStore } from "@/lib/store";

export function SetAlertDialog({
  open,
  onOpenChange,
  analysis,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  analysis: Analysis;
}) {
  const { quote, suggestedTrigger, triggerDirection, smartAction } = analysis;
  const addAlert = useWatchStore((s) => s.addAlert);
  const setZone = useWatchStore((s) => s.setZone);
  const [price, setPrice] = useState(String(suggestedTrigger));
  const [direction, setDirection] = useState<"below" | "above">(triggerDirection);

  const numeric = Number(price.replace(/,/g, ""));
  const valid = Number.isFinite(numeric) && numeric > 0;

  function submit() {
    if (!valid) return;
    setZone(quote.symbol, numeric);
    addAlert({
      symbol: quote.symbol,
      trigger: numeric,
      direction,
      note: smartAction,
    });
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <div className="mb-5 pr-8">
          <DialogTitle>Set price alert</DialogTitle>
          <DialogDescription className="mt-1">
            Turn the smart signal into a watch condition.
          </DialogDescription>
        </div>

        <div className="rounded-lg bg-elevated p-4 border border-border/40">
          <p className="font-mono text-sm tracking-wide text-muted font-semibold">{quote.symbol}</p>
          <p className="mt-1 font-mono text-2xl tabular-nums font-bold text-fg">{formatInr(quote.price)}</p>
          <p className="mt-3 text-sm text-fg">{smartAction}</p>
        </div>

        <div className="mt-5 grid gap-3">
          <div className="grid gap-1.5">
            <Label htmlFor="trigger">Trigger price</Label>
            <Input
              id="trigger"
              inputMode="decimal"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="font-mono tabular-nums"
            />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant={direction === "below" ? "default" : "outline"}
              onClick={() => setDirection("below")}
            >
              At or below
            </Button>
            <Button
              type="button"
              variant={direction === "above" ? "default" : "outline"}
              onClick={() => setDirection("above")}
            >
              At or above
            </Button>
          </div>
        </div>

        <Button className="mt-5 w-full" onClick={submit} disabled={!valid}>
          <svg className="size-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          Set alert
        </Button>
      </DialogContent>
    </Dialog>
  );
}
