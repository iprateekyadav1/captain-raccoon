import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "default" | "sm" | "lg" | "icon";
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "default", asChild = false, ...props }, ref) => {
    const Comp = asChild ? "span" : "button";
    
    const variants = {
      primary: "bg-brand-blue text-white hover:bg-blue-600 shadow-sm transition-all shadow-brand-blue/20",
      secondary: "bg-brand-bg border border-brand-border text-brand-text hover:bg-gray-50 transition-all",
      outline: "border-2 border-brand-blue text-brand-blue hover:bg-brand-blue/5 transition-all",
      ghost: "text-brand-muted hover:bg-gray-100 hover:text-brand-text transition-all",
    };

    const sizes = {
      default: "h-11 px-5 py-2 rounded-lg font-medium",
      sm: "h-9 px-4 rounded-md text-sm",
      lg: "h-14 px-8 rounded-xl text-lg font-semibold",
      icon: "h-10 w-10 rounded-full flex items-center justify-center",
    };

    return (
      <Comp
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue cursor-pointer disabled:pointer-events-none disabled:opacity-50",
          variants[variant],
          sizes[size],
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
