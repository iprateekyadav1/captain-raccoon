"use client";

import * as React from "react";
import { motion, useScroll, useTransform, useSpring } from "framer-motion";

// ═══════════════════════════════════════════════════════════
//  CAROUSEL PERSPECTIVE — Scroll-driven global camera effect
//
//  Replaced the broken fixed+overflow-hidden approach.
//  Now a normal in-flow wrapper with a perspective "camera"
//  that subtly tilts as you scroll — so all sections remain
//  visible and actually scroll as expected.
// ═══════════════════════════════════════════════════════════

interface CarouselPerspectiveProps {
  children: React.ReactNode;
}

export function CarouselPerspective({ children }: CarouselPerspectiveProps) {
  const { scrollYProgress } = useScroll();

  // Very subtle global rotateX — simulates a tilting overhead camera
  const rawRotateX = useTransform(scrollYProgress, [0, 0.5, 1], [1.5, 0, -1.5]);
  const rotateX    = useSpring(rawRotateX, { stiffness: 40, damping: 25 });

  // Mild scale: barely perceptible zoom at the mid-point of the page
  const rawScale = useTransform(scrollYProgress, [0, 0.5, 1], [1, 1.012, 1]);
  const scale    = useSpring(rawScale, { stiffness: 40, damping: 25 });

  return (
    // Outer div: sets CSS perspective (the "camera distance")
    <div
      style={{
        perspective: "1800px",
        perspectiveOrigin: "50% 0%",
        overflowX: "hidden",
      }}
    >
      {/* Inner: receives the camera tilt + scale transforms */}
      <motion.div
        style={{
          rotateX,
          scale,
          transformStyle: "preserve-3d",
          transformOrigin: "center top",
        }}
      >
        {children}
      </motion.div>
    </div>
  );
}
