import * as React from "react";
import { cn } from "@/lib/utils";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-11 w-full rounded-md bg-elevated px-3.5 text-sm text-fg shadow-[var(--shadow-border)]",
        "placeholder:text-faint outline-none transition-[box-shadow] duration-150",
        "focus-visible:shadow-[0_0_0_1px_var(--color-primary)]",
        "disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
