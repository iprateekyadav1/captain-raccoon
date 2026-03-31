"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, useScroll, useSpring, useTransform } from "framer-motion";
import { Syne } from "next/font/google";

// UI Components
import SmoothScroll from "@/components/ui/SmoothScroll";
import ThreeDCard from "@/components/ui/ThreeDCard";
import FloatingAsset from "@/components/ui/FloatingAsset";
import { withBasePath } from "@/lib/asset-path";

const syne = Syne({
  subsets: ["latin"],
  weight: ["400", "700", "800"],
  display: "swap",
  variable: "--font-syne",
});

export default function PromoPage() {
  const [activeStage, setActiveStage] = useState(0); 
  const sectionRefs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const index = Number(entry.target.getAttribute("data-index"));
            setActiveStage(index);
          }
        });
      },
      {
        root: null,
        rootMargin: "-40% 0px -40% 0px",
        threshold: 0,
      }
    );

    sectionRefs.current.forEach((sec) => {
      if (sec) observer.observe(sec);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <SmoothScroll>
      <div className={`relative w-full min-h-screen bg-[#14b8a6] text-white overflow-hidden font-sans ${syne.variable}`}>
        
        {/* ── CSS Noise Overlay ── */}
        <div 
          className="fixed inset-0 pointer-events-none mix-blend-overlay z-50 opacity-[0.08]"
          style={{
            backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=\"0 0 200 200\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Cfilter id=\"noiseFilter\"%3E%3CfeTurbulence type=\"fractalNoise\" baseFrequency=\"0.8\" numOctaves=\"3\" stitchTiles=\"stitch\"/%3E%3C/filter%3E%3Crect width=\"100%25\" height=\"100%25\" filter=\"url(%23noiseFilter)\"/%3E%3C/svg%3E')",
          }}
        />

        {/* ── Floating 3D Background Elements ── */}
        <FloatingAsset src="/threed-anchor.png" alt="Anchor" className="top-[10%] left-[5%] w-32 h-32 opacity-40 blur-[1px]" speed={0.2} rotateSpeed={120} />
        <FloatingAsset src="/threed-coin.png" alt="Coin" className="top-[40%] right-[10%] w-24 h-24 opacity-60" speed={0.4} rotateSpeed={-180} />
        <FloatingAsset src="/threed-compass.png" alt="Compass" className="top-[70%] left-[15%] w-40 h-40 opacity-50 blur-[2px]" speed={0.3} rotateSpeed={90} />
        <FloatingAsset src="/threed-anchor.png" alt="Anchor" className="top-[120%] right-[5%] w-48 h-48 opacity-30" speed={0.25} rotateSpeed={-60} direction="down" />
        <FloatingAsset src="/threed-coin.png" alt="Coin" className="top-[180%] left-[8%] w-16 h-16 opacity-70" speed={0.5} rotateSpeed={240} />

        {/* ── Sticky Character (Enhanced with Framer Motion) ── */}
        <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-30">
          <div className="max-w-7xl mx-auto h-full relative">
            
            <motion.div
              layout
              transition={{ type: "spring", stiffness: 100, damping: 20, mass: 1 }}
              className={`absolute bottom-0 left-1/2 -translate-x-1/2 overflow-hidden`}
              animate={{
                width: activeStage === 0 ? 500 : activeStage === 1 ? 300 : activeStage === 2 ? 450 : activeStage === 3 ? 350 : 150,
                height: activeStage === 0 ? 500 : activeStage === 1 ? 300 : activeStage === 2 ? 450 : activeStage === 3 ? 350 : 150,
                x: activeStage === 1 ? "-400px" : activeStage === 2 ? "200px" : "0px",
                y: activeStage === 1 ? "12px" : activeStage === 2 ? "-40px" : activeStage === 3 ? "40px" : "0px",
                translateY: activeStage === 0 ? "96px" : "0px",
                translateX: "-50%",
              }}
              style={{ WebkitMaskImage: "radial-gradient(ellipse at center, black 50%, transparent 70%)" }}
            >
              <AnimatePresence mode="wait">
                <motion.img
                  key={activeStage}
                  initial={{ opacity: 0, y: 20, rotateY: 45 }}
                  animate={{ opacity: 1, y: 0, rotateY: 0 }}
                  exit={{ opacity: 0, y: -20, rotateY: -45 }}
                  transition={{ duration: 0.4 }}
                  src={
                    activeStage === 0 ? withBasePath("/raccoon-waving.webp") :
                    activeStage === 1 ? withBasePath("/raccoon-pointing.webp") :
                    activeStage === 2 ? withBasePath("/raccoon-surprised.webp") :
                    withBasePath("/raccoon-sitting.webp")
                  }
                  alt="Captain Raccoon"
                  loading="lazy"
                  decoding="async"
                  className="absolute bottom-0 object-contain w-full h-full drop-shadow-[0_20px_50px_rgba(0,0,0,0.5)]"
                />
              </AnimatePresence>
            </motion.div>
          </div>
        </div>

        {/* ── 1. Hero Section ── */}
        <section 
          data-index="0" 
          ref={(el) => { sectionRefs.current[0] = el; }}
          className="relative w-full min-h-screen flex items-center justify-center pt-20 pb-40 px-6 z-20"
        >
          <div className="max-w-7xl mx-auto w-full h-full relative">
            <motion.div 
              initial={{ opacity: 0, y: 100 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
              className="max-w-2xl translate-y-[-10vh]"
            >
              <h1 className="font-[family-name:--font-syne] font-extrabold text-[clamp(4rem,9vw,8rem)] text-white leading-[0.9] tracking-tight drop-shadow-2xl">
                Captain<br/>Raccoon.
              </h1>
              <p className="mt-6 text-2xl text-teal-100/90 max-w-lg font-medium">
                The guardian of the harbor is ready for an absurdly adorable adventure. 
              </p>
              <button className="group mt-8 px-8 py-4 bg-white text-teal-600 rounded-full font-bold text-lg hover:scale-110 active:scale-95 transition-all shadow-xl hover:shadow-2xl hover:shadow-white/20 relative overflow-hidden">
                <span className="relative z-10">Meet the Captain</span>
                <div className="absolute inset-0 bg-teal-50 scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
              </button>
            </motion.div>
          </div>
        </section>

        {/* ── 2. Features Section (Points to the side) ── */}
        <section 
          data-index="1"
          ref={(el) => { sectionRefs.current[1] = el; }}
          className="w-full min-h-screen py-32 px-6 flex items-center relative z-20"
        >
          <div className="max-w-7xl mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-12">
            <div className="hidden md:block"></div>
            
            <div className="flex flex-col gap-8 md:pl-20">
               <h2 className="font-[family-name:--font-syne] font-bold text-5xl mb-8">What makes him the best?</h2>
               
               {[
                 { title: "Sharp Claws", desc: "Perfect for climbing ropes and causing mild, harmless chaos." },
                 { title: "Night Vision", desc: "Navigating the murky docks like an absolute professional." },
                 { title: "Cute Hat", desc: "Instantly commands respect from local seagulls." },
               ].map((f, i) => (
                 <ThreeDCard key={i} intensity={10}>
                   <div className="bg-white/10 backdrop-blur-md p-6 rounded-3xl border border-white/20 flex gap-4 items-start h-full">
                     <div className="relative w-16 h-16 bg-white/20 rounded-full flex-shrink-0 flex justify-center items-center text-3xl shadow-inner border border-white/30 overflow-hidden">
                        <img src={withBasePath("/hero-raccoon.webp")} alt="Icon" loading="lazy" decoding="async" className="absolute -bottom-2 w-12 h-12 object-cover rounded-full" />
                     </div>
                     <div>
                       <h3 className="font-bold text-xl">{f.title}</h3>
                       <p className="text-teal-50 mt-2">{f.desc}</p>
                     </div>
                   </div>
                 </ThreeDCard>
               ))}
            </div>
          </div>
        </section>

        {/* ── 3. Testimonials (Surprised at numbers) ── */}
        <section 
          data-index="2"
          ref={(el) => { sectionRefs.current[2] = el; }}
           className="w-full min-h-screen py-32 px-6 flex items-center bg-black/10 relative z-20"
        >
          <div className="max-w-7xl mx-auto w-full">
             <h2 className="font-[family-name:--font-syne] font-bold text-5xl text-center mb-16">Whispers at the Pier</h2>
             
             <div className="flex flex-col md:flex-row gap-8 justify-center items-center">
               
               <div className="flex-1 text-center md:text-left md:pr-12 md:pb-32">
                 <motion.p 
                    className="text-8xl font-[family-name:--font-syne] font-bold text-white mb-2"
                    initial={{ scale: 0.5, opacity: 0 }}
                    whileInView={{ scale: 1, opacity: 1 }}
                    transition={{ type: "spring", stiffness: 200 }}
                 >99%</motion.p>
                 <p className="text-xl text-teal-100 font-medium">of pirates are terrified<br/>when he stares from the fog.</p>
               </div>

               <div className="flex-1">
                 <ThreeDCard intensity={15}>
                    <div className="bg-white text-teal-900 p-8 rounded-[3rem] rounded-bl-[4rem] shadow-2xl relative translate-y-24 h-full">
                        <div className="absolute -top-12 -right-6 w-24 h-24 overflow-hidden rounded-full border-4 border-[#14b8a6] bg-teal-800 shadow-xl z-30">
                          <img src={withBasePath("/hero-raccoon.webp")} alt="Peeking" loading="lazy" decoding="async" className="w-full h-full object-cover translate-y-2" />
                        </div>
                        
                        <p className="text-2xl font-medium leading-relaxed mt-4">
                          "I was losing all my fish, but then Captain Raccoon showed up. He didn't stop the fish stealing... he just stole them first."
                        </p>
                        <div className="mt-6 flex items-center gap-4 border-t border-teal-100 pt-6">
                          <div className="w-12 h-12 bg-teal-200 rounded-full" />
                          <div>
                            <strong className="block text-lg">Old Pete</strong>
                            <span className="text-teal-700/60 text-sm font-bold uppercase">Local Fisherman</span>
                          </div>
                        </div>
                    </div>
                 </ThreeDCard>
               </div>
             </div>
          </div>
        </section>

        {/* ── 4. Pricing (Character sitting) ── */}
        <section
          data-index="3"
          ref={(el) => { sectionRefs.current[3] = el; }}
          className="w-full min-h-screen flex flex-col justify-center py-32 px-6 relative z-20"
        >
          <div className="max-w-7xl mx-auto w-full">
            <h2 className="font-[family-name:--font-syne] font-bold text-5xl text-center mb-6">Hire the Captain</h2>
            <p className="text-xl text-center mb-20 max-w-2xl mx-auto text-teal-100">
               Yes, you have to pay a raccoon. The economy is tough. Pick your tier wisely!
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 pt-10">
              <ThreeDCard intensity={5}>
                <div className="bg-black/10 border border-white/20 p-8 pt-12 rounded-3xl backdrop-blur-md relative overflow-hidden flex flex-col items-center text-center h-full">
                  <div className="absolute -top-6 -left-6 w-24 h-24 rotate-[-15deg] opacity-60 mix-blend-multiply">
                     <img src={withBasePath("/raccoon-pointing.webp")} alt="Sad" loading="lazy" decoding="async" className="w-full h-full object-contain grayscale" />
                  </div>
                  <h3 className="text-2xl font-bold mt-4">Standard Ration</h3>
                  <p className="text-5xl font-[family-name:--font-syne] font-bold mt-4">$0 <span className="text-xl text-teal-100 font-sans font-normal">/mo</span></p>
                  <ul className="mt-8 space-y-4 text-left w-full">
                    <li className="flex gap-2 text-teal-50"><span className="opacity-50">🐟</span> One dried fish</li>
                    <li className="flex gap-2 text-teal-50"><span className="opacity-50">🐾</span> Wave from a distance</li>
                  </ul>
                </div>
              </ThreeDCard>
              
              <ThreeDCard intensity={15} className="md:-translate-y-8">
                <div className="bg-white text-teal-900 border-4 border-[#0d9488] p-8 pt-6 rounded-3xl shadow-[0_30px_100px_rgba(0,0,0,0.3)] flex flex-col items-center text-center relative z-10 h-full">
                  <div className="uppercase font-bold tracking-widest text-xs text-white bg-[#0d9488] px-4 py-1 rounded-full mb-6">Most Popular</div>
                  <div className="w-20 h-20 bg-teal-100 rounded-full mb-2 overflow-hidden border-2 border-teal-300">
                     <img src={withBasePath("/raccoon-waving.webp")} alt="Happy" loading="lazy" decoding="async" className="w-full h-full object-cover translate-y-2 scale-110" />
                  </div>
                  <h3 className="text-2xl font-bold">First Mate</h3>
                  <p className="text-5xl font-[family-name:--font-syne] font-bold mt-2">$29 <span className="text-xl text-teal-600 font-sans font-normal">/mo</span></p>
                  <ul className="mt-8 space-y-4 font-medium text-left w-full pb-8">
                    <li className="flex gap-2"><span>🍪</span> Unlimited cookies</li>
                    <li className="flex gap-2"><span>⚓</span> Harbor tours</li>
                    <li className="flex gap-2"><span>👀</span> Stares at you</li>
                  </ul>
                  <button className="w-full mt-auto bg-[#14b8a6] text-white font-bold py-4 rounded-full hover:bg-[#0d9488] transition-colors shadow-lg">
                    Choose Plan
                  </button>
                </div>
              </ThreeDCard>
              
              <ThreeDCard intensity={5}>
                <div className="bg-[#0d9488] border border-teal-400 p-8 pt-12 rounded-3xl shadow-lg relative overflow-hidden flex flex-col items-center text-center text-white h-full">
                  <div className="absolute top-0 right-0 w-32 h-32 translate-x-4 -translate-y-4 mix-blend-multiply opacity-50">
                     <img src={withBasePath("/raccoon-surprised.webp")} alt="Shocked" loading="lazy" decoding="async" className="w-full h-full object-contain" />
                  </div>
                  <h3 className="text-2xl font-bold mt-4 text-white">Fleet Admiral</h3>
                  <p className="text-5xl font-[family-name:--font-syne] font-bold mt-4 text-white">$99 <span className="text-xl text-teal-200 font-sans font-normal">/mo</span></p>
                  <ul className="mt-8 space-y-4 text-left w-full text-teal-50">
                    <li className="flex gap-2"><span>艇</span> Ownership of pier</li>
                    <li className="flex gap-2"><span>🏴‍☠️</span> Pirate immunity</li>
                  </ul>
                </div>
              </ThreeDCard>
            </div>
          </div>
        </section>

        {/* ── 5. Footer (Tiny waving raccoon) ── */}
        <section 
          data-index="4"
          ref={(el) => { sectionRefs.current[4] = el; }}
          className="w-full h-[50vh] bg-[#0d9488] flex flex-col justify-end items-center pb-8 border-t border-teal-500 relative z-20"
        >
           <motion.h2 
            initial={{ y: 50, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            className="font-[family-name:--font-syne] font-bold text-6xl text-center mb-auto pt-20"
           >
            Ready to set sail?
           </motion.h2>
           <p className="font-mono text-xs text-teal-200 uppercase tracking-widest">© 2026 Captain Raccoon Studios</p>
        </section>

      </div>
    </SmoothScroll>
  );
}
