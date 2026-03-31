"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "home",      href: "#hero" },
  { name: "character", href: "#character" },
  { name: "episodes",  href: "#timeline" },
  { name: "map",       href: "#map" },
  { name: "gallery",   href: "#gallery" },
];

export function Navbar({ className }: { className?: string }) {
  const [active, setActive] = React.useState("home");
  const [visible, setVisible] = React.useState(true);
  const [scrolled, setScrolled] = React.useState(false);
  const lastScrollY = React.useRef(0);

  React.useEffect(() => {
    const sections = navItems
      .map((item) => document.querySelector(item.href))
      .filter((node): node is HTMLElement => node instanceof HTMLElement);
    let rafId = 0;

    const update = () => {
      rafId = 0;
      const y = window.scrollY;
      setVisible(y < lastScrollY.current || y < 80);
      setScrolled(y > 50);
      lastScrollY.current = y;

      for (const item of [...navItems].reverse()) {
        const el = sections.find((section) => `#${section.id}` === item.href);
        if (el && el.getBoundingClientRect().top <= 120) {
          setActive(item.name);
          break;
        }
      }
    };

    const handler = () => {
      if (rafId) return;
      rafId = window.requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", handler, { passive: true });
    return () => {
      if (rafId) {
        window.cancelAnimationFrame(rafId);
      }
      window.removeEventListener("scroll", handler);
    };
  }, []);

  const scrollTo = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    const el = document.querySelector(href);
    if (el) {
      const top = el.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top, behavior: "smooth" });
    }
  };

  return (
    <nav
      className={cn(
        "fixed top-4 left-1/2 -translate-x-1/2 z-50",
        "flex items-center gap-0.5 px-1.5 py-1.5",
        scrolled
          ? "bg-zinc-950/80 backdrop-blur-xl border-white/[0.06]"
          : "bg-transparent border-transparent",
        "border rounded-sm",
        "transition-all duration-500",
        visible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-4 pointer-events-none",
        className
      )}
    >
      {/* Bracket accent — left */}
      <span className="text-zinc-700 font-mono text-xs mr-1 hidden md:inline select-none">{"["}</span>

      {navItems.map((item) => (
        <a
          key={item.name}
          href={item.href}
          onClick={(e) => { scrollTo(e, item.href); setActive(item.name); }}
          className={cn(
            "relative px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.15em] transition-all duration-200",
            active === item.name
              ? "text-cyan-400"
              : "text-zinc-500 hover:text-zinc-200"
          )}
        >
          {item.name}
          {active === item.name && (
            <span className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 w-3 h-px bg-cyan-400" />
          )}
        </a>
      ))}

      {/* Bracket accent — right */}
      <span className="text-zinc-700 font-mono text-xs ml-1 hidden md:inline select-none">{"]"}</span>
    </nav>
  );
}
