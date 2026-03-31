import * as React from "react";
import { cn } from "@/lib/utils";

export const Section = React.forwardRef<
  HTMLElement,
  React.HTMLAttributes<HTMLElement>
>(({ className, ...props }, ref) => (
  <section
    ref={ref}
    className={cn("py-16 md:py-24 w-full relative", className)}
    {...props}
  />
));
Section.displayName = "Section";

export const Container = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("container mx-auto px-4 md:px-8 max-w-7xl", className)}
    {...props}
  />
));
Container.displayName = "Container";
