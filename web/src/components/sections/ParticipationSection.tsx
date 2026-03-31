"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Section, Container } from "@/components/ui/layout";

const presets = [
  "Explore the forest at dawn",
  "Patrol the village docks",
  "Investigate a strange light at sea",
];

export function ParticipationSection() {
  const [idea, setIdea] = React.useState("");
  const [submitted, setSubmitted] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (idea.trim()) {
      setSubmitted(true);
      setTimeout(() => { setSubmitted(false); setIdea(""); }, 5000);
    }
  };

  return (
    <Section id="participation" className="py-20" style={{ transformStyle: "preserve-3d" }}>
      <Container className="max-w-2xl">
        {/* Section label */}
        <div className="flex items-center gap-3 mb-10">
          <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
          <span className="text-cyan-400 text-xs font-semibold uppercase tracking-widest">shape the story</span>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="rounded-2xl border border-white/[0.07] bg-zinc-900 p-8"
          style={{ transform: "translateZ(80px)" }}
        >
          <h2 className="font-display font-black text-3xl text-zinc-100 mb-2">
            What should Captain<br />Raccoon do next?
          </h2>
          <p className="text-zinc-500 text-sm mb-8 leading-relaxed">
            The harbor is unpredictable. Your choices influence the next chapter.
          </p>

          {submitted ? (
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="py-12 flex flex-col items-center text-center gap-4"
            >
              <div className="w-14 h-14 rounded-full bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center text-cyan-400 text-xl">✓</div>
              <h3 className="text-zinc-100 font-bold text-xl">Idea received!</h3>
              <p className="text-zinc-500 text-sm">Captain Raccoon is considering your suggestion.</p>
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <textarea
                id="idea"
                rows={3}
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder="Describe what Captain Raccoon should do..."
                required
                className="w-full bg-zinc-950 border border-white/[0.07] rounded-xl p-4 text-zinc-200 text-sm placeholder:text-zinc-700 focus:border-cyan-400/40 focus:ring-1 focus:ring-cyan-400/20 outline-none transition-all resize-none"
              />

              <div className="flex flex-wrap gap-2">
                {presets.map((p, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setIdea(p)}
                    className="text-xs px-3 py-1.5 rounded-full border border-white/[0.07] text-zinc-400 hover:border-cyan-400/30 hover:text-cyan-400 transition-all"
                  >
                    {p}
                  </button>
                ))}
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="email"
                  placeholder="Email (optional)"
                  className="flex-1 bg-zinc-950 border border-white/[0.07] rounded-xl px-4 py-3 text-zinc-300 text-sm placeholder:text-zinc-700 focus:border-cyan-400/40 outline-none transition-all"
                />
                <button
                  type="submit"
                  className="px-6 py-3 rounded-xl bg-cyan-400 text-zinc-950 font-bold text-sm hover:bg-cyan-300 transition-colors shadow-[0_0_24px_rgba(34,211,238,0.2)]"
                >
                  Send Idea →
                </button>
              </div>
            </form>
          )}
        </motion.div>
      </Container>
    </Section>
  );
}
