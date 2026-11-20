import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "studio" | "studio-accent";
  size?: "default" | "sm" | "lg" | "icon" | "xs";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";

    const variantStyles = {
      default: "bg-zinc-100 text-zinc-900 hover:bg-zinc-200 shadow-sm",
      destructive: "bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20",
      outline: "border border-white/10 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-200",
      secondary: "bg-zinc-800 text-zinc-200 hover:bg-zinc-700",
      ghost: "hover:bg-white/5 text-zinc-300 hover:text-white",
      link: "text-sky-400 underline-offset-4 hover:underline",
      studio: "bg-zinc-900/80 border border-white/10 text-zinc-100 hover:border-sky-500/50 hover:bg-zinc-800 transition-all",
      "studio-accent": "bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-medium shadow-lg shadow-sky-500/20 transition-all active:scale-[0.98]",
    }[variant];

    const sizeStyles = {
      default: "h-9 px-4 py-2 text-sm",
      sm: "h-8 rounded-md px-3 text-xs",
      xs: "h-7 rounded px-2 text-[11px]",
      lg: "h-11 rounded-md px-8 text-base",
      icon: "h-8 w-8",
    }[size];

    return (
      <Comp
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-lg font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sky-500 disabled:pointer-events-none disabled:opacity-50 select-none",
          variantStyles,
          sizeStyles,
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
