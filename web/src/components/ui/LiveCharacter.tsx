"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Maximize2, Minimize2, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

export function LiveCharacter() {
  const [isVisible, setIsVisible] = React.useState(true);
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [showTooltip, setShowTooltip] = React.useState(true);

  React.useEffect(() => {
    // Hide initial tooltip after 8 seconds
    const timer = setTimeout(() => setShowTooltip(false), 8000);
    return () => clearTimeout(timer);
  }, []);

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end pointer-events-none">
      
      {/* Ambient message bubble */}
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            className="mb-4 bg-brand-navy border border-brand-teal/50 shadow-lg rounded-2xl p-4 max-w-[200px] pointer-events-auto"
          >
            <p className="text-sm text-brand-offwhite leading-relaxed">
              *Hums a sailor's tune* The tide is coming in... take a look around!
            </p>
            {/* Tooltip pointer */}
            <div className="absolute -bottom-2 right-8 w-4 h-4 bg-brand-navy border-b border-r border-brand-teal/50 rotate-45" />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        layout
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 20 }}
        className={cn(
          "relative overflow-hidden rounded-full border-2 border-brand-amber/50 shadow-[0_0_30px_rgba(255,170,0,0.15)] bg-brand-navy transition-all duration-500 pointer-events-auto cursor-pointer group hover:shadow-[0_0_40px_rgba(255,170,0,0.3)]",
          isExpanded ? "w-64 h-64 md:w-80 md:h-80 rounded-2xl" : "w-24 h-24 md:w-32 md:h-32"
        )}
        onClick={() => {
          if(!isExpanded) setShowTooltip(false);
        }}
      >
        {/* Replace with provided video asset: public/captain-raccoon-idle.mp4 */}
        <video
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover opacity-90 mix-blend-screen"
          src="/captain-raccoon-video.mp4"
          onError={(e) => {
            // Fallback if video isn't there yet
            e.currentTarget.style.display = 'none';
          }}
        />
        
        {/* Fallback image if video fails or is missing */}
        <div className="absolute inset-0 -z-10 bg-[url('https://placehold.co/400x400/0B132B/FFD166?text=Capt+Raccoon+Live')] bg-cover bg-center" />

        <div className="absolute inset-0 bg-gradient-to-t from-brand-navy/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-end pb-4 space-y-2">
          
          {/* Controls */}
          <div className="flex gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="p-2 bg-brand-navy/80 rounded-full text-brand-amber hover:bg-brand-teal transition-colors"
            >
              {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowTooltip(!showTooltip);
              }}
              className="p-2 bg-brand-navy/80 rounded-full text-brand-offwhite hover:bg-brand-teal transition-colors"
            >
              <MessageSquare size={16} />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsVisible(false);
              }}
              className="p-2 bg-brand-navy/80 rounded-full text-red-400 hover:bg-red-400/20 transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

      </motion.div>
    </div>
  );
}
