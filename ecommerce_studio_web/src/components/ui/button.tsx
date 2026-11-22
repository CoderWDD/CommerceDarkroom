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
      default: "bg-blue-600 text-white hover:bg-blue-700 shadow-sm active:scale-[0.99]",
      destructive: "bg-red-50 text-red-600 border border-red-200 hover:bg-red-100",
      outline: "border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 hover:border-slate-300 shadow-xs",
      secondary: "bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-200/80",
      ghost: "hover:bg-slate-100 text-slate-600 hover:text-slate-900",
      link: "text-blue-600 underline-offset-4 hover:underline",
      studio: "bg-white border border-slate-200 text-slate-700 hover:border-blue-500/50 hover:text-blue-600 hover:bg-slate-50 transition-all shadow-xs",
      "studio-accent": "bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white font-semibold shadow-md shadow-amber-500/20 transition-all active:scale-[0.98]",
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
          "inline-flex items-center justify-center whitespace-nowrap rounded-lg font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50 select-none",
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
