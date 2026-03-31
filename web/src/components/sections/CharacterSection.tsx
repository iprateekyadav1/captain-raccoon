"use client";

import { motion } from "framer-motion";
import { Section, Container } from "@/components/ui/layout";
import { Shield, Eye, BookOpen, Compass } from "lucide-react";
import React from "react";

const traits = [
  { icon: Shield,   title: "Night Watch",    desc: "Protector of the piers after dark",          color: "text-red-400" },
  { icon: BookOpen, title: "Storyteller",    desc: "Every tide brings a new tale to keep",       color: "text-sky-500" },
  { icon: Eye,      title: "Sharp Senses",   desc: "Sees through harbor fog and deception",      color: "text-amber-500" },
  { icon: Compass,  title: "Harbor Guide",   desc: "Navigating the lost to safety",              color: "text-emerald-500" },
];

export function CharacterSection() {
  return (
    <Section id="character" className="relative pt-32 pb-48 bg-doc-charcoal z-10 jagged-top" style={{ transformStyle: "preserve-3d" }}>
      {/* ── Background Dossier Texture ── */}
      <div className="absolute inset-0 opacity-5 pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(circle at 50% 50%, #fff 2px, transparent 2px)', backgroundSize: '40px 40px' }} />

      <Container className="relative z-10">
        
        {/* Section label - Dossier Tab */}
        <div className="inline-flex items-center gap-3 mb-16 bg-doc-olive border border-white/10 px-4 py-2 shadow-xl -rotate-1 origin-bottom-left">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="font-mono text-cyan-400 text-xs font-semibold uppercase tracking-widest">
            FILE_01 // TARGET_PROFILE
          </span>
        </div>

        {/* ── Evidence Board Layout ── */}
        <div className="flex flex-col lg:flex-row gap-12 lg:gap-20 items-start">
          
          {/* LEFT: Polaroid Stack */}
          <motion.div 
            initial={{ opacity: 0, x: -40, rotate: -5 }}
            whileInView={{ opacity: 1, x: 0, rotate: -2 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className="w-full lg:w-5/12 relative min-h-[500px]"
            style={{ transform: "translateZ(60px)" }}
          >
            {/* Background Note */}
            <div className="absolute -top-6 -right-4 bg-yellow-100/90 w-48 p-4 shadow-lg rotate-3 z-0 font-display text-doc-charcoal text-sm"
                 style={{ backgroundImage: 'linear-gradient(transparent 90%, rgba(0,0,0,0.1) 90%)', backgroundSize: '100% 1.5rem', lineHeight: '1.5rem' }}>
              <span className="font-bold text-red-600 block mb-1">URGENT:</span>
              Subject sighted again. 
              Who acts as the guardian of the piers?
              <br/><br/>
              - Harbor Master
            </div>

            {/* Main Polaroid */}
            <div className="polaroid absolute top-0 left-0 w-full max-w-sm z-10" style={{ '--rand': '0.7' } as React.CSSProperties}>
              <div className="relative aspect-[3/4] overflow-hidden bg-black mb-4 outline outline-1 outline-black/10">
                <img
                  src="/hero-raccoon.png"
                  alt="Captain Raccoon Surveillance"
                  className="w-full h-full object-cover filter contrast-125 saturate-50 sepia-[.2]"
                />
                <div className="absolute top-2 right-2 font-mono text-red-500 text-[10px] bg-white/80 px-1 rounded-sm shadow-sm backdrop-blur-sm">
                  REC •
                </div>
              </div>
              <div className="text-center font-mono text-doc-charcoal text-sm uppercase font-bold border-b border-black/20 pb-1 w-3/4 mx-auto border-dashed">
                SUBJECT: CAPT. RACCOON
              </div>
              <p className="text-center font-sans text-xs text-doc-charcoal/60 mt-1 italic">
                Sighting #042 - Midnight
              </p>
              {/* Tape Graphic */}
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-24 h-8 bg-white/40 backdrop-blur-sm -rotate-2" 
                   style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}/>
            </div>
          </motion.div>

          {/* RIGHT: Typewriter Text & Traits */}
          <div className="w-full lg:w-7/12 flex flex-col gap-10 mt-12 lg:mt-0 lg:ml-8 relative z-20"
               style={{ transform: "translateZ(80px)" }}>
            
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <h2 className="font-display font-black text-5xl md:text-7xl text-doc-paper leading-[0.9] tracking-tighter mb-6 uppercase text-stroke-white">
                Who is<br/><span className="text-transparent bg-clip-text bg-doc-paper" style={{ WebkitTextStroke: '0px' }}>Captain Raccoon?</span>
              </h2>
              <div className="bg-doc-navy-light/50 p-6 md:p-8 border-l-4 border-cyan-400 relative">
                {/* Paper fold effect */}
                <div className="absolute top-0 right-0 w-8 h-8 bg-gradient-to-bl from-doc-charcoal to-doc-charcoal-light shadow-[-2px_2px_2px_rgba(0,0,0,0.2)]" />
                <p className="font-mono text-doc-paper/80 text-sm leading-relaxed mb-6">
                  "He's not a pirate, and he's not looking for trouble. A small, sturdy figure with realistic black-and-grey fur and a thickly striped tail — Captain Raccoon is the self-appointed Night Watch of the piers."
                </p>
                <p className="font-display text-cyan-400 font-bold tracking-wider uppercase text-xs">
                  QUOTE ON RECORD: <span className="text-white/80 normal-case italic">"No small traveler left alone."</span>
                </p>
              </div>
            </motion.div>

            {/* Traits Collection */}
            <motion.div 
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-4"
            >
              {traits.map((t, i) => (
                <div key={t.title} className="flex items-start gap-4 p-4 bg-doc-paper text-doc-charcoal rounded-sm shadow-md transition-transform hover:-translate-y-1 hover:shadow-lg">
                  <div className={`mt-1 p-2 bg-doc-navy rounded-sm ${t.color}`}>
                    <t.icon size={18} />
                  </div>
                  <div>
                    <h4 className="font-mono font-bold text-sm uppercase tracking-wide border-b border-doc-charcoal/10 pb-1 mb-1">{t.title}</h4>
                    <p className="text-xs leading-relaxed opacity-80">{t.desc}</p>
                  </div>
                </div>
              ))}
            </motion.div>

            {/* Fact Grid */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="mt-4 p-6 border-2 border-white/5 border-dashed"
            >
              <div className="flex flex-wrap justify-between gap-6 font-mono">
                {[
                  { label: "Location",   value: "Harbor Village" },
                  { label: "Role",       value: "Night Watch" },
                  { label: "Fur_Type",   value: "Black & Grey" },
                  { label: "Eye_Color",  value: "Amber glow" },
                ].map((f) => (
                  <div key={f.label}>
                    <p className="text-cyan-400/60 text-[9px] uppercase tracking-widest font-bold mb-1">[{f.label}]</p>
                    <p className="text-white font-semibold text-sm">{f.value}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </Container>
    </Section>
  );
}
