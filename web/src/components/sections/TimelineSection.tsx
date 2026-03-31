"use client";

import { motion } from "framer-motion";
import { Section, Container } from "@/components/ui/layout";
import { Play } from "lucide-react";

const episodes = [
  {
    id: "01",
    title: "Footsteps on the Pier",
    desc: "A heavy fog rolls in, masking the approaching sounds of a lost traveler.",
    img: "https://placehold.co/500x700/18181b/ef4444?text=Ep.+01",
    accent: "from-red-500",
    tag: "origin",
  },
  {
    id: "02",
    title: "The Lantern's Glow",
    desc: "A mysterious artifact washes ashore — glowing, warm, and undeniably alive.",
    img: "https://placehold.co/500x700/18181b/22d3ee?text=Ep.+02",
    accent: "from-cyan-500",
    tag: "mystery",
  },
  {
    id: "03",
    title: "Shadows in the Sails",
    desc: "An abandoned vessel drifts into the harbor.",
    img: "https://placehold.co/500x700/18181b/facc15?text=Ep.+03",
    accent: "from-yellow-500",
    tag: "danger",
  },
  {
    id: "04",
    title: "The Village Remembers",
    desc: "Old harbor folk share stories of a disappearing captain.",
    img: "https://placehold.co/500x700/18181b/34A853?text=Ep.+04",
    accent: "from-green-500",
    tag: "lore",
    upcoming: true,
  },
];

export function TimelineSection() {
  return (
    <Section id="timeline" className="py-24 bg-doc-charcoal relative z-0" style={{ transformStyle: "preserve-3d" }}>
      <Container>
        {/* Section label */}
        <div className="flex flex-col md:flex-row items-baseline justify-between mb-16 gap-6">
          <div className="inline-flex items-center gap-3 bg-doc-navy border border-white/5 py-2 px-4 shadow-lg -rotate-1">
            <div className="w-2 h-2 bg-red-500" />
            <span className="text-red-500 text-xs font-mono font-bold uppercase tracking-[0.2em]">
              FILE_02 // SURVEILLANCE LOGS
            </span>
          </div>
          <span className="text-doc-paper/40 font-serif italic text-sm">"The evidence trails off into the fog..."</span>
        </div>

        {/* Staggered Field Reports Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 md:gap-4 pb-8">
          {episodes.map((ep, i) => {
            // Pseudo-random rotations and margins to look like scattered photos
            const rotations = ["-rotate-3", "rotate-2", "-rotate-1", "rotate-4"];
            const margins = ["mt-0", "mt-8", "mt-2", "mt-12"];

            return (
              <motion.div
                key={ep.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.6, delay: i * 0.1 }}
                className={`${margins[i % 4]} flex justify-center w-full`}
              >
                <div className={`relative group w-full max-w-[280px] polaroid ${rotations[i % 4]} hover:rotate-0 hover:scale-105 transition-all duration-300 hover:z-50 cursor-pointer`}
                     style={{ 
                       '--rand': Math.random().toString(),
                       transform: `translateZ(${40 + i * 15}px)` 
                     } as React.CSSProperties}>
                  
                  {/* Tape Graphic */}
                  <div className={`absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-6 bg-white/40 backdrop-blur-sm shadow-sm z-20 ${i % 2 === 0 ? '-rotate-3' : 'rotate-2'}`} />

                  {/* Stamp for upcoming */}
                  {ep.upcoming && (
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 border-4 border-red-600/80 text-red-600/80 font-black text-2xl uppercase tracking-widest p-2 rotate-[-15deg] mix-blend-multiply whitespace-nowrap">
                      Classified
                    </div>
                  )}

                  {/* Image Container */}
                  <div className={`relative aspect-[3/4] overflow-hidden bg-black outline outline-1 outline-black/20 mb-3 ${ep.upcoming ? "grayscale opacity-50 contrast-125" : "filter contrast-125 saturate-50 sepia-[.1]"}`}>
                    <img
                      src={ep.img}
                      alt={ep.title}
                      className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                    />
                    
                    {/* Timestamp overlay */}
                    <div className="absolute bottom-2 left-2 font-mono text-white/80 text-[10px] bg-black/40 px-1">
                      LOG_{ep.id}:00:00
                    </div>

                    {!ep.upcoming && (
                      <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="w-12 h-12 rounded-full border-2 border-white/80 flex items-center justify-center bg-black/20 backdrop-blur-sm">
                          <Play className="text-white ml-1" size={20} fill="white" />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Paper details */}
                  <div className="flex flex-col h-full font-mono text-doc-charcoal">
                    <div className="flex justify-between items-baseline border-b border-black/20 pb-1 mb-2 border-dashed">
                      <span className="text-xs font-bold uppercase tracking-widest text-red-600">
                        Vol.{ep.id}
                      </span>
                      <span className="text-[9px] uppercase tracking-wider text-doc-charcoal/60 bg-black/5 px-1">
                        [{ep.tag}]
                      </span>
                    </div>

                    <h3 className="font-display font-black text-lg leading-tight mb-2 uppercase">
                      {ep.title}
                    </h3>
                    
                    <p className="font-serif italic text-xs leading-relaxed text-doc-charcoal/80 mb-2">
                       "{ep.desc}"
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </Container>
    </Section>
  );
}
