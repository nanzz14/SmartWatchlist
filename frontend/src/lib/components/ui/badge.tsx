import React from "react";
import { cn } from "@/lib/utils";

export type BadgeVariant = "default" | "live" | "warn" | "down" | "outline";

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-elevated text-muted",
  live: "bg-up/12 text-up",
  warn: "bg-warn/12 text-warn",
  down: "bg-down/12 text-down",
  outline: "shadow-[var(--shadow-border)] text-muted",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium tracking-wide",
        variantStyles[variant] || variantStyles.default,
        className
      )}
      {...props}
    />
  );
}
