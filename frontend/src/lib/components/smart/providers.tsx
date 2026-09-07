import React from "react";
import { TooltipProvider } from "@/lib/components/ui/tooltip";

export function AppProviders({ children }: { children: React.ReactNode }) {
  return <TooltipProvider>{children}</TooltipProvider>;
}
