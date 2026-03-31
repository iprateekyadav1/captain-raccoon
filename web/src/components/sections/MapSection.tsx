"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Section, Container } from "@/components/ui/layout";

function seededRandom(seed: number): number {
  const x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
}

const locations = [
  { id: "pier",    title: "The Old Pier",    desc: "Where the story begins.",             x: 20, y: 70, episodes: "01, 02", color: "#ef4444" },
  { id: "village", title: "Animal Village",  desc: "Cozy burrows and tree homes.",        x: 60, y: 40, episodes: "03",     color: "#22d3ee" },
  { id: "lookout", title: "Cliff Lookout",   desc: "Highest peak to spot distant ships.", x: 80, y: 15, episodes: "04",     color: "#facc15" },
];

export function MapSection() {
  const [activeLoc, setActiveLoc] = React.useState<string | null>(null);

  return (
    <Section id="map" className="py-24 bg-doc-olive relative z-10 jagged-bottom border-b-8 border-doc-charcoal" style={{ transformStyle: "preserve-3d" }}>
      {/* ── Topographic/Grid background texture ── */}
      <div className="absolute inset-0 opacity-10 pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)', backgroundSize: '2rem 2rem' }} />

      <Container className="relative z-10">
        
        {/* Label - Tactical Folder Tab */}
        <div className="inline-flex items-center gap-3 mb-12 bg-doc-charcoal border border-white/10 px-4 py-2 shadow-xl rotate-1 origin-top-left group">
          <div className="w-2 h-2 bg-yellow-400" />
          <span className="font-mono text-yellow-400 text-xs font-bold uppercase tracking-widest">
            FILE_03 // RECONNAISSANCE MAP
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* ── Physical Nautical Chart Map ── */}
          <div className="lg:col-span-8 relative aspect-square md:aspect-[16/9] bg-[#dfddd1] rounded-sm p-2 shadow-2xl transform rotate-1"
               style={{ transform: "translateZ(80px) rotate(-1deg)" }}>
            {/* The actual map surface */}
            <div className="relative w-full h-full bg-[#e8e5dc] border border-black/10 overflow-hidden shadow-inner">
              
              {/* Paper creases */}
              <div className="absolute inset-0 flex">
                <div className="w-1/3 h-full border-r border-black/5" />
                <div className="w-1/3 h-full border-r border-black/5" />
              </div>
              <div className="absolute inset-0 flex flex-col">
                <div className="w-full h-1/2 border-b border-black/5" />
              </div>

              {/* Topo lines (SVG) */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.03]" xmlns="http://www.w3.org/2000/svg">
                {Array.from({ length: 8 }).map((_, i) => (
                  <path key={i} d={`M 0 ${80 + i * 10} Q ${30 + i * 20} ${50 - i * 5} ${50 + i * 15} ${70 + i * 5} T 100 ${60 + i * 12}`} stroke="#000" strokeWidth="1" fill="none" vectorEffect="non-scaling-stroke" preserveAspectRatio="none" />
                ))}
              </svg>

              {/* Stains & Noise */}
              <div className="absolute inset-0 opacity-[0.04]" style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=\"0 0 200 200\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Cfilter id=\"noiseFilter\"%3E%3CfeTurbulence type=\"fractalNoise\" baseFrequency=\"0.65\" numOctaves=\"3\" stitchTiles=\"stitch\"/%3E%3C/filter%3E%3Crect width=\"100%25\" height=\"100%25\" filter=\"url(%23noiseFilter)\"/%3E%3C/svg%3E')" }} />

              {/* Hand-drawn route lines (red marker) */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40 mix-blend-multiply" xmlns="http://www.w3.org/2000/svg">
                <path d="M 20 70 L 60 40 L 80 15" stroke="#ef4444" strokeWidth="3" strokeDasharray="6 6" fill="none" vectorEffect="non-scaling-stroke" strokeLinecap="round" />
              </svg>

              {/* Push-Pins */}
              {locations.map((loc) => (
                <div
                  key={loc.id}
                  className="absolute"
                  style={{ left: `${loc.x}%`, top: `${loc.y}%` }}
                  onMouseEnter={() => setActiveLoc(loc.id)}
                  onMouseLeave={() => setActiveLoc(null)}
                >
                  <div className="relative -ml-3 w-6 h-6 flex justify-center -mt-6"> {/* Pin point is at the bottom center */}
                    {/* Shadow */}
                    <div className="absolute bottom-0 w-2 h-1 bg-black/40 rounded-full blur-[2px] translate-x-2 translate-y-2" />
                    
                    {/* Pin Graphic */}
                    <div className="w-4 h-6 bg-gradient-to-br from-white to-gray-400 rounded-t-full shadow-md z-10 cursor-pointer hover:scale-110 origin-bottom transition-transform" style={{ borderTopColor: loc.color, borderTopWidth: '8px' }}>
                      <div className="w-[2px] h-3 bg-zinc-300 mx-auto mt-2 shadow-inner" />
                    </div>

                    {/* Tooltip */}
                    {activeLoc === loc.id && (
                      <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-48 p-3 bg-doc-paper border-2 border-doc-charcoal shadow-[4px_4px_0_rgba(17,17,17,1)] z-20 pointer-events-none"
                      >
                        <h4 className="text-doc-charcoal font-black text-sm mb-1 uppercase tracking-tight">{loc.title}</h4>
                        <p className="text-doc-charcoal/80 text-xs leading-relaxed mb-2 font-serif italic">"{loc.desc}"</p>
                        <span className="inline-block text-[10px] font-bold px-1 bg-doc-charcoal text-white font-mono uppercase">
                          REF: EP_{loc.episodes}
                        </span>
                        {/* Triangle pointer */}
                        <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[8px] border-l-transparent border-r-transparent border-t-doc-charcoal ml-[-2px]" />
                        <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[4px] border-r-[4px] border-t-[6px] border-l-transparent border-r-transparent border-t-doc-paper" />
                      </motion.div>
                    )}
                  </div>
                </div>
              ))}

              {/* Map stamp */}
              <div className="absolute bottom-6 right-6 border-4 border-red-500/20 text-red-500/30 font-bold uppercase tracking-widest text-xl rotate-[-15deg] p-1 pointer-events-none mix-blend-multiply">
                RESTRICTED
              </div>
            </div>
            
            {/* Paper clip graphic */}
            <div className="absolute -top-4 left-8 w-4 h-12 border-2 border-gray-400 rounded-full -rotate-6 shadow-sm z-20" />
            <div className="absolute -top-3 left-9 w-4 h-10 border-2 border-gray-300 rounded-full -rotate-6 z-20" />
          </div>

          {/* ── Right side: Location Coordinates List ── */}
          <div className="lg:col-span-4 flex flex-col gap-4"
               style={{ transform: "translateZ(100px)" }}>
            <div className="bg-doc-olive-light p-4 mb-2 shadow-inner border border-black/20">
              <p className="font-mono text-[10px] text-yellow-400/80 mb-2 uppercase">System Message</p>
              <p className="font-mono text-xs text-white/80">Select a push-pin on the chart to read field notes regarding identified landmarks.</p>
            </div>
            
            {locations.map((loc) => (
              <div
                key={loc.id}
                className={`p-4 border-l-4 bg-doc-charcoal cursor-default transition-all duration-200 shadow-md flex gap-4
                  ${activeLoc === loc.id ? "scale-[1.02] border-yellow-400" : "border-white/10 hover:border-white/30"}`}
                onMouseEnter={() => setActiveLoc(loc.id)}
                onMouseLeave={() => setActiveLoc(null)}
              >
                <div className="flex-shrink-0 w-8 h-8 rounded-sm flex items-center justify-center font-mono text-xs font-bold bg-white/5 text-white/50" style={{ color: activeLoc === loc.id ? loc.color : '' }}>
                  0{locations.indexOf(loc)+1}
                </div>
                <div>
                  <h4 className="text-zinc-100 font-bold text-sm uppercase mb-1">{loc.title}</h4>
                  <p className="text-zinc-400 text-xs font-serif italic mb-2">"{loc.desc}"</p>
                  <p className="text-cyan-400 text-[10px] font-mono tracking-widest">SEE LOGS: {loc.episodes}</p>
                </div>
              </div>
            ))}
          </div>

        </div>
      </Container>
    </Section>
  );
}
