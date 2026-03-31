"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Section, Container } from "@/components/ui/layout";

const filters = ["all", "character", "locations", "cinematic"];

const items = [
  {
    id: 1,
    cat: "character",
    type: "video",
    src: "/Captain_Raccoon_on_202603220010.mp4",
    title: "Captain Raccoon",
    desc: "Origin episode",
    style: "col-span-12 md:col-span-7 aspect-[4/3] md:-ml-8",
  },
  {
    id: 2,
    cat: "cinematic",
    type: "video",
    src: "/2026-03-18T17-09-07_establishing_drone_watermarked.mp4",
    title: "Establishing Shot",
    desc: "Drone — harbor approach",
    style: "col-span-12 md:col-span-5 md:mt-24 aspect-square",
  },
  {
    id: 3,
    cat: "character",
    type: "video",
    src: "/Captain_Raccoon_on_202603220023.mp4",
    title: "Night Watch",
    desc: "Episode 02",
    style: "col-span-12 md:col-span-4 aspect-[3/4] md:ml-12 -mt-12 z-10",
  },
  {
    id: 4,
    cat: "locations",
    type: "video",
    src: "/2026-03-18T16-38-49_top_down_aerial_shot_watermarked.mp4",
    title: "Aerial — Harbour",
    desc: "Top-down overview",
    style: "col-span-12 md:col-span-8 aspect-video mt-8",
  },
  {
    id: 5,
    cat: "character",
    type: "image",
    src: "/hero-raccoon.png",
    title: "AI Portrait",
    desc: "Character art",
    style: "col-span-12 md:col-span-5 aspect-[3/4] md:mt-[-100px]",
  },
  {
    id: 6,
    cat: "locations",
    type: "video",
    src: "/2026-03-18T16-41-03_extreme_overhead_top_watermarked.mp4",
    title: "Overhead Grid",
    desc: "Extreme top-down",
    style: "col-span-12 md:col-span-7 aspect-[16/6] mt-12 md:-mr-12",
  },
  {
    id: 7,
    cat: "cinematic",
    type: "video",
    src: "/Captain_Raccoon_on_202603220025.mp4",
    title: "Harbour Dusk",
    desc: "Episode 03",
    style: "col-span-12 md:col-span-6 aspect-video mb-12",
  },
  {
    id: 8,
    cat: "locations",
    type: "video",
    src: "/2026-03-18T16-46-01_top_down_overhead_watermarked.mp4",
    title: "Pier Overhead",
    desc: "Location scout",
    style: "col-span-12 md:col-span-6 md:mt-24 aspect-square",
  },
];

type Item = typeof items[number];

function CollageTile({ item, i }: { item: Item; i: number }) {
  const [hovered, setHovered] = React.useState(false);
  const videoRef = React.useRef<HTMLVideoElement>(null);

  React.useEffect(() => {
    if (!videoRef.current) return;
    if (hovered) {
      videoRef.current.play().catch(() => {});
    } else {
      videoRef.current.pause();
    }
  }, [hovered]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.8, delay: i * 0.1 }}
      className={`relative group ${item.style}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{ transform: `translateZ(${20 + i * 10}px)` }}
    >
      {/* Editorial Numbering */}
      <div className="absolute -left-4 -top-6 text-[8rem] font-display font-black text-transparent text-stroke-white opacity-20 pointer-events-none z-0 mix-blend-overlay">
        0{item.id}
      </div>

      <div className="relative w-full h-full overflow-hidden border-2 border-doc-charcoal bg-doc-navy shadow-xl z-10 transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-[1.02]">
        {item.type === "video" ? (
          <video
            ref={videoRef}
            src={item.src}
            muted
            loop
            playsInline
            preload="metadata"
            className="absolute inset-0 w-full h-full object-cover filter transition-all duration-700 saturate-50 contrast-125 group-hover:saturate-100 group-hover:contrast-100"
          />
        ) : (
          <img
            src={item.src}
            alt={item.title}
            className="absolute inset-0 w-full h-full object-cover filter transition-all duration-700 saturate-50 contrast-125 group-hover:saturate-100 group-hover:contrast-100"
          />
        )}
        
        {/* Playback Badge (Tactical Style) */}
        {item.type === "video" && (
          <div className="absolute top-4 left-4 flex items-center gap-2 px-2 py-1 bg-doc-charcoal/80 border border-white/20 backdrop-blur-sm z-20">
             <div className={`w-1.5 h-1.5 ${hovered ? "bg-red-500 animate-pulse" : "bg-white/50"}`} />
             <span className="text-[10px] font-mono text-white/80 uppercase tracking-widest">{hovered ? "PLAYING" : "STANDBY"}</span>
          </div>
        )}

        {/* Hover Info Overlay */}
        <div className="absolute inset-0 bg-doc-charcoal/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-6 z-20">
          <div className="bg-doc-paper p-4 transform translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
             <p className="text-cyan-600 font-mono text-[10px] uppercase tracking-widest border-b border-black/10 pb-1 mb-1">{item.cat}</p>
             <h4 className="text-doc-charcoal font-black text-lg uppercase tracking-tight leading-none">{item.title}</h4>
             <p className="text-doc-charcoal/60 text-xs italic font-serif mt-1">"{item.desc}"</p>
          </div>
        </div>
      </div>

      {/* Scattered Footnote */}
      <div className={`hidden md:block absolute top-1/2 -translate-y-1/2 ${i % 2 === 0 ? '-right-24' : '-left-24 text-right'} w-48 font-mono text-[9px] text-white/30 uppercase tracking-widest pointer-events-none rotate-90 origin-center mix-blend-overlay`}>
        REF_IMG_00{item.id} // CLASSIFIED
        <br/>
        COORD: {Math.floor(Math.random() * 90)}°N {Math.floor(Math.random() * 180)}°E
      </div>
    </motion.div>
  );
}

export function GallerySection() {
  const [filter, setFilter] = React.useState("all");
  const filtered = items.filter((i) => filter === "all" || i.cat === filter);

  return (
    <Section id="gallery" className="py-24 bg-doc-navy relative z-0" style={{ transformStyle: "preserve-3d" }}>
      {/* Torn Edge transition from Timeline / Map */}
      <div className="absolute inset-0 opacity-5 pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]" />

      <Container className="relative z-10">
        {/* Header - Editorial Style */}
        <div className="flex flex-col md:flex-row items-baseline justify-between gap-6 mb-24 border-b border-white/10 pb-8">
          <div>
            <h2 className="font-display font-black text-6xl text-doc-paper leading-none uppercase tracking-tighter mb-2">
              Visual<br/>Evidence
            </h2>
            <p className="text-white/40 font-mono text-xs tracking-widest uppercase">Archive // 2026.03</p>
          </div>

          {/* Filter pills - Tactical Switches */}
          <div className="flex flex-wrap gap-3">
            {filters.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 text-[10px] font-mono uppercase tracking-widest transition-all border
                  ${filter === f
                    ? "bg-doc-paper text-doc-charcoal border-doc-paper shadow-[0_0_10px_rgba(255,255,255,0.2)]"
                    : "border-white/20 text-white/50 hover:border-white/40 hover:text-white/80"}`}
              >
                [{f}]
              </button>
            ))}
          </div>
        </div>

        {/* Masonry / Collage Grid Layout */}
        <motion.div layout className="grid grid-cols-12 gap-y-16 md:gap-y-24 gap-x-6">
          {filtered.map((item, i) => (
            <CollageTile key={item.id} item={item} i={i} />
          ))}
        </motion.div>
      </Container>
    </Section>
  );
}
