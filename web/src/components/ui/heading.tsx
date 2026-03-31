import * as React from "react";
import { cn } from "@/lib/utils";

export interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: "h1" | "h2" | "h3" | "h4";
  as?: "h1" | "h2" | "h3" | "h4" | "p" | "span";
}

export const Heading = React.forwardRef<HTMLHeadingElement, HeadingProps>(
  ({ className, level = "h2", as, ...props }, ref) => {
    const Tag = as || level;

    const sizes = {
      h1: "text-4xl lg:text-7xl font-black tracking-tight",
      h2: "text-3xl lg:text-5xl font-bold tracking-tight",
      h3: "text-2xl lg:text-3xl font-semibold",
      h4: "text-xl font-medium",
    };

    return (
      <Tag
        ref={ref}
        className={cn(
          "font-display text-brand-text leading-tight",
          sizes[level],
          className
        )}
        {...props}
      />
    );
  }
);
Heading.displayName = "Heading";
