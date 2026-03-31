"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Section, Container } from "@/components/ui/layout";
import { Play, Pause, SkipBack, SkipForward } from "lucide-react";

const scriptBeats = [
  { time: "00:00", text: "The camera pans over the murky harbor water. Fog horns in the distance." },
  { time: "00:15", text: "Captain Raccoon adjusts his lantern, ears twitching at every sound." },
  { time: "00:45", text: "A sudden splash near the old dock. Something — or someone — fell in." },
  { time: "01:20", text: "He rushes to the edge, peering into the dark water below." },
];

export function LiveEpisodeSection() {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [activeBeat, setActiveBeat] = React.useState(0);

  React.useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying) {
      interval = setInterval(() => {
        setActiveBeat((prev) => (prev + 1) % scriptBeats.length);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  const toggle = () => {
    setIsPlaying(!isPlaying);
    const vid = document.getElementById("story-video") as HTMLVideoElement;
    if (vid) isPlaying ? vid.pause() : vid.play();
  };

  return (
    <Section id="live-episode" className="py-20" style={{ transformStyle: "preserve-3d" }}>
      <Container>
        {/* Section label */}
        <div className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-3">
            <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            <span className="text-red-400 text-xs font-semibold uppercase tracking-widest">live episode</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Video player */}
          <div className="lg:col-span-2 rounded-2xl border border-white/[0.07] bg-zinc-900 overflow-hidden group"
               style={{ transform: "translateZ(60px)" }}>
            <div className="relative aspect-video">
              {/* Actual video */}
              <video
                id="story-video"
                className="absolute inset-0 w-full h-full object-cover"
                loop
                playsInline
              >
                <source src="/Captain_Raccoon_on_202603220023.mp4" type="video/mp4" />
                <source src="/Captain_Raccoon_on_202603220025.mp4" type="video/mp4" />
                <source src="/Captain_Raccoon_on_202603220010.mp4" type="video/mp4" />
              </video>
              {/* Placeholder */}
              <div className="absolute inset-0 bg-gradient-to-br from-zinc-900 via-zinc-800 to-cyan-950 flex flex-col items-center justify-center">
                <div className="text-5xl mb-3 select-none">🦝</div>
                <p className="text-zinc-600 font-mono text-[10px] tracking-widest uppercase">place captain-raccoon-story.mp4 in /public</p>
              </div>

              {/* Play overlay */}
              <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={toggle}
                  className="w-16 h-16 rounded-full bg-zinc-900/90 border border-cyan-400/40 text-cyan-400 flex items-center justify-center hover:scale-110 hover:bg-cyan-400/10 transition-all shadow-[0_0_30px_rgba(34,211,238,0.2)]"
                >
                  {isPlaying ? <Pause size={24} /> : <Play size={24} className="ml-1" />}
                </button>
              </div>
            </div>

            {/* Controls bar */}
            <div className="px-5 h-12 flex items-center justify-between border-t border-white/[0.06]">
              <div className="flex items-center gap-4">
                <button className="text-zinc-600 hover:text-zinc-300 transition-colors"><SkipBack size={16} /></button>
                <button onClick={toggle} className="text-cyan-400 hover:text-cyan-300 transition-colors">
                  {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                </button>
                <button className="text-zinc-600 hover:text-zinc-300 transition-colors"><SkipForward size={16} /></button>
              </div>
              <span className="text-zinc-600 font-mono text-[11px]">{scriptBeats[activeBeat].time} / 05:00</span>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                <span className="text-red-400 text-[10px] font-semibold uppercase tracking-wider">Live</span>
              </div>
            </div>
          </div>

          {/* Director's notes */}
          <div className="rounded-2xl border border-white/[0.07] bg-zinc-900 p-5 overflow-y-auto max-h-[360px] lg:max-h-none"
               style={{ transform: "translateZ(90px)" }}>
            <div className="flex items-center gap-2 mb-5 pb-4 border-b border-white/[0.06]">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <h4 className="text-zinc-300 text-sm font-semibold">Director's Notes</h4>
            </div>
            <div className="space-y-2">
              {scriptBeats.map((beat, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className={`p-3 rounded-xl border-l-2 transition-all duration-300 cursor-pointer
                    ${activeBeat === i
                      ? "border-cyan-400 bg-cyan-400/5 text-zinc-200"
                      : "border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-zinc-400"}`}
                  onClick={() => setActiveBeat(i)}
                >
                  <span className="text-[10px] font-mono font-bold text-cyan-400/70 block mb-1">{beat.time}</span>
                  <p className="text-xs leading-relaxed">{beat.text}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </Container>
    </Section>
  );
}
