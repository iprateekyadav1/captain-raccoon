"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { WarpStarfield } from "@/components/ui/WarpStarfield";

// ═══════════════════════════════════════════════════════
//  HERO SECTION — Cinematic full-bleed opening
//  Inspired by RetroNova's HUD aesthetic:
//    • full-viewport video background (NOT in a card)
//    • corner-pinned metadata (coordinates, time, status)
//    • massive condensed typography
//    • scan-line texture overlay
//    • warp starfield underneath
// ═══════════════════════════════════════════════════════

function LiveClock() {
  const [time, setTime] = React.useState("");
  React.useEffect(() => {
    const tick = () => {
      const now = new Date();
      setTime(
        `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return <>{time}</>;
}

export function HeroSection() {
  return (
    <section
      id="hero"
      className="relative h-screen w-full flex flex-col justify-end overflow-hidden"
      style={{ transformStyle: "preserve-3d" }}
    >


      {/* ── Layer 2: Color grading overlay ── */}
      <div
        className="absolute inset-0 z-[2] pointer-events-none"
        style={{
          background: `
            linear-gradient(180deg, rgba(9,9,11,0.6) 0%, transparent 30%, transparent 50%, rgba(9,9,11,0.85) 100%),
            linear-gradient(90deg, rgba(9,9,11,0.4) 0%, transparent 50%)
          `,
        }}
      />

      {/* ── Layer 3: Scan-line texture (RetroNova-inspired CRT effect) ── */}
      <div
        className="absolute inset-0 z-[3] pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: `repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(255,255,255,0.4) 2px,
            rgba(255,255,255,0.4) 4px
          )`,
          backgroundSize: "100% 4px",
        }}
      />

      {/* ── HUD: Top-left metadata ── */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3, duration: 0.8 }}
        className="absolute top-6 left-6 z-10"
        style={{ transform: "translateZ(100px)" }}
      >
        <div className="flex items-center gap-2 mb-2">
          <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span className="font-mono text-cyan-400 text-[10px] tracking-[0.25em] uppercase font-bold">
            system: active
          </span>
        </div>
        <div className="font-mono text-zinc-600 text-[10px] leading-relaxed tracking-wider">
          <p>[time: <span className="text-zinc-400"><LiveClock /></span>]</p>
          <p>[coord: 45.1°N, 14.3°E]</p>
          <p>[mission: harbor recon]</p>
        </div>
      </motion.div>

      {/* ── HUD: Top-right version/status ── */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.4, duration: 0.8 }}
        className="absolute top-6 right-6 z-10 font-mono text-right text-[10px] tracking-wider"
        style={{ transform: "translateZ(80px)" }}
      >
        <p className="text-zinc-600">[v 1.0.3]</p>
        <p className="text-zinc-600">[build: stable]</p>
        <div className="mt-2 flex items-center gap-1.5 justify-end">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          <span className="text-red-400 font-bold uppercase tracking-[0.2em]">live broadcast</span>
        </div>
      </motion.div>

      {/* ── HUD: Left edge — rotated label ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 1 }}
        className="absolute left-4 top-1/2 -translate-y-1/2 z-10 hidden md:block"
      >
        <p
          className="font-mono text-zinc-700 text-[9px] tracking-[0.4em] uppercase"
          style={{ writingMode: "vertical-lr", textOrientation: "mixed" }}
        >
          [s] version 1.3 — interactive
        </p>
      </motion.div>

      {/* ── HUD: Right edge — rotated label ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7, duration: 1 }}
        className="absolute right-4 top-1/2 -translate-y-1/2 z-10 hidden md:block"
      >
        <p
          className="font-mono text-zinc-700 text-[9px] tracking-[0.4em] uppercase"
          style={{ writingMode: "vertical-rl", textOrientation: "mixed" }}
        >
          {"/// stories from the quiet harbors"}
        </p>
      </motion.div>

      {/* ── Main content: Massive condensed title, bottom-left ── */}
      <div className="relative z-10 w-full h-full flex flex-col justify-end pointer-events-none pb-20">
        
        {/* Title — MASSIVE, bleeding off screen like Pokemon History */}
        <motion.div
          initial={{ opacity: 0, scale: 1.05 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className="w-full flex flex-col items-center justify-center -mb-8 md:-mb-16"
        >
          <h1 className="font-display font-black uppercase leading-[0.75] tracking-tighter text-center"
              style={{ fontSize: "clamp(6rem, 20vw, 24rem)" }}>
            <span className="block text-zinc-100 mix-blend-overlay">Captain</span>
            <span className="block text-stroke-white opacity-80 mix-blend-plus-lighter">
              Raccoon
            </span>
          </h1>
        </motion.div>

        {/* Bottom bar: description + stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="max-w-7xl mx-auto w-full px-6 flex flex-col md:flex-row items-end justify-between gap-8 pointer-events-auto"
        >
          <div className="max-w-sm bg-doc-charcoal/80 p-6 border border-white/10 backdrop-blur-md rounded-sm shadow-2xl relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-cyan-400/50" />
            <p className="font-mono text-cyan-400 text-[10px] tracking-[0.2em] uppercase mb-4">
              // Subject: The Guardian
            </p>
            <p className="text-doc-paper text-sm leading-relaxed mb-6 font-serif italic">
              "He's not a pirate. He's not looking for trouble. But the harbor has secrets, and only one figure roams the piers at night."
            </p>
            <div className="flex flex-wrap gap-3">
              <a
                href="#timeline"
                onClick={(e) => {
                  e.preventDefault();
                  document.querySelector("#timeline")?.scrollIntoView({ behavior: "smooth" });
                }}
                className="group px-5 py-2 bg-doc-paper text-doc-navy font-mono font-bold text-[10px] uppercase tracking-wider hover:bg-white transition-colors"
              >
                [Access Log]
              </a>
              <a
                href="#character"
                onClick={(e) => {
                  e.preventDefault();
                  document.querySelector("#character")?.scrollIntoView({ behavior: "smooth" });
                }}
                className="px-5 py-2 border border-doc-paper/30 text-doc-paper font-mono text-[10px] uppercase tracking-wider hover:bg-doc-paper/10 transition-colors"
              >
                [View Profile]
              </a>
            </div>
          </div>

          {/* Stats — monospace, typewriter style */}
          <div className="flex gap-6 md:gap-10 pb-2">
            {[
              { value: "03", label: "episodes" },
              { value: "05", label: "locations" },
              { value: "∞",  label: "choices" },
            ].map((s) => (
              <div key={s.label} className="text-right">
                <p className="font-mono font-bold text-3xl md:text-5xl text-doc-paper">{s.value}</p>
                <p className="font-mono text-cyan-400/60 text-[9px] tracking-[0.2em] uppercase mt-1">
                  {s.label}
                </p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* ── HUD: Bottom center — system status bar ── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2, duration: 0.6 }}
        className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-4 w-full max-w-lg px-6"
      >
        <div className="flex-1 h-[1px] bg-white/20" />
        <span className="font-mono text-white/40 text-[9px] tracking-[0.3em] uppercase">
          surveillance feed active
        </span>
        <div className="flex-1 h-[1px] bg-white/20" />
      </motion.div>

      {/* ── HUD: Target Crosshairs ── */}
      <div className="absolute inset-0 z-10 pointer-events-none flex items-center justify-center opacity-20">
        <div className="w-[400px] h-[400px] border border-cyan-400/30 rounded-full" />
        <div className="absolute w-[420px] h-[1px] bg-cyan-400/30" />
        <div className="absolute w-[1px] h-[420px] bg-cyan-400/30" />
      </div>

      {/* ── HUD: Code block — bottom right ── */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.8, duration: 0.8 }}
        className="absolute bottom-32 right-8 z-10 hidden lg:block"
        style={{ transform: "translateZ(120px)" }}
      >
        <div className="border border-white/10 p-4 font-mono text-[10px] leading-relaxed bg-black/40 backdrop-blur-sm text-doc-paper max-w-[260px] shadow-2xl shadow-black/50">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/10">
            <span className="text-cyan-400 tracking-wider">OBSERVATION_LOG</span>
            <div className="w-2 h-2 rounded-full border border-cyan-400/50 flex align-center justify-center">
               <div className="w-1 h-1 bg-cyan-400 rounded-full self-center animate-pulse" />
            </div>
          </div>
          <p className="text-white/60 mb-1">{"<ENTRY 749>"}</p>
          <p className="text-white/80 italic">"Subject spotted near Pier 4. Moving silently. Fur pattern confirmed."</p>
          <p className="text-cyan-400/60 mt-2 text-[8px] tracking-widest text-right">END_LOG</p>
        </div>
      </motion.div>
    </section>
  );
}
