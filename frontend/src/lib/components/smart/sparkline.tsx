import { cn } from "@/lib/utils";

export function Sparkline({
  data,
  className,
  tone = "muted",
}: {
  data: number[];
  className?: string;
  tone?: "up" | "down" | "muted";
}) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const w = 128;
  const h = 36;
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / span) * (h - 2) - 1;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className={cn(
        "overflow-visible",
        tone === "up" && "text-up",
        tone === "down" && "text-down",
        tone === "muted" && "text-muted",
        className,
      )}
      aria-hidden
    >
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
        strokeLinecap="round"
        points={pts}
      />
    </svg>
  );
}

export function RangeTrack({
  low,
  high,
  value,
}: {
  low: number;
  high: number;
  value: number;
}) {
  const span = high - low || 1;
  const pct = Math.min(100, Math.max(0, ((value - low) / span) * 100));
  return (
    <div className="relative h-1 rounded-full bg-elevated">
      <div
        className="absolute top-1/2 size-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary"
        style={{ left: `${pct}%` }}
      />
    </div>
  );
}
