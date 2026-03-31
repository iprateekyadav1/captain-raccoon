"use client";

import { Container } from "@/components/ui/layout";

const links = {
  Story: ["Episodes", "Characters", "World Map", "Gallery"],
  Community: ["Discord", "Forum", "Fan Art", "Newsletter"],
  About: ["The Project", "Contact", "Privacy", "Terms"],
};

export function Footer() {
  return (
    <footer className="relative overflow-hidden border-t border-white/[0.06] mt-10" style={{ transformStyle: "preserve-3d" }}>
      {/* Cyan glow at bottom center */}
      <div className="pointer-events-none absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[200px] bg-cyan-500/5 blur-[80px]" />

      <Container className="pt-16 pb-10 relative z-10">
        {/* Main footer row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1" style={{ transform: "translateZ(40px)" }}>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-cyan-400 font-bold text-lg">#</span>
              <span className="font-display font-black text-zinc-100">Captain Raccoon</span>
            </div>
            <p className="text-zinc-600 text-xs leading-relaxed max-w-[180px]">
              A live storytelling world from the quiet harbors.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(links).map(([heading, items]) => (
            <div key={heading}>
              <h5 className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-3">{heading}</h5>
              <ul className="space-y-2">
                {items.map((item) => (
                  <li key={item}>
                    <a href="#" className="text-zinc-500 text-xs hover:text-cyan-400 transition-colors">{item}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Massive wordmark */}
        <div className="border-t border-white/[0.04] pt-8" style={{ transform: "translateZ(20px)" }}>
          <p
            className="font-display font-black text-zinc-900 select-none leading-none pointer-events-none"
            style={{ fontSize: "clamp(3rem, 14vw, 12rem)", letterSpacing: "-0.04em" }}
          >
            CAPTAIN<br />
            <span className="text-transparent" style={{ WebkitTextStroke: "1px rgba(255,255,255,0.06)" }}>
              RACCOON
            </span>
          </p>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 mt-8 pt-6 border-t border-white/[0.04]">
          <p className="text-zinc-700 text-xs">© 2026 Captain Raccoon. All rights reserved.</p>
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 rounded-full bg-cyan-400/60" />
            <span className="text-zinc-700 text-xs font-mono">stories from the quiet harbors</span>
          </div>
        </div>
      </Container>
    </footer>
  );
}
