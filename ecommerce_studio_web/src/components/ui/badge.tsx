import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "copilot" | "tag";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantStyles = {
    default: "border border-slate-200 bg-slate-100 text-slate-700",
    secondary: "border border-slate-200/80 bg-slate-50 text-slate-600",
    destructive: "border border-red-200 bg-red-50 text-red-700 font-medium",
    outline: "border border-slate-200 text-slate-500 bg-white",
    success: "border border-emerald-200 bg-emerald-50 text-emerald-700 font-medium",
    warning: "border border-amber-200 bg-amber-50 text-amber-700 font-medium",
    copilot: "border border-indigo-200 bg-indigo-50 text-indigo-700 font-medium",
    tag: "border border-slate-200 bg-white hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 text-slate-600 cursor-pointer transition-all",
  }[variant];

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-blue-500 select-none",
        variantStyles,
        className
      )}
      {...props}
    />
  );
}

export { Badge };
