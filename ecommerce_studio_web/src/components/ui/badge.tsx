import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "copilot" | "tag";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantStyles = {
    default: "border-transparent bg-zinc-800 text-zinc-200",
    secondary: "border-transparent bg-zinc-800/80 text-zinc-300",
    destructive: "border-rose-500/30 bg-rose-500/10 text-rose-400",
    outline: "border-white/10 text-zinc-400",
    success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
    warning: "border-amber-500/30 bg-amber-500/10 text-amber-400",
    copilot: "border-indigo-500/30 bg-indigo-500/10 text-indigo-300",
    tag: "border-white/10 bg-zinc-900/80 text-zinc-300 hover:border-sky-500/40 hover:text-sky-300 cursor-pointer transition-colors",
  }[variant];

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500 select-none",
        variantStyles,
        className
      )}
      {...props}
    />
  );
}

export { Badge };
