"use client";

import * as React from "react";
import { motion, useScroll, useTransform, useSpring } from "framer-motion";

// ═══════════════════════════════════════════════════════
//  SCROLL 3D SECTION — Scroll-driven 3D reveal per section
//
//  As the section enters the viewport it tilts from a slight
//  rotateX angle (looking "into" the screen) down to flat.
//  Background elements get a subtle translateZ parallax.
// ═══════════════════════════════════════════════════════

interface Scroll3DSectionProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  /** How far the section tips back at entry (degrees). Default 12 */
  entryAngle?: number;
  /** Disable the 3D effect (e.g. on the hero which has its own effects) */
  flat?: boolean;
}

export function Scroll3DSection({
  children,
  className,
  style,
  entryAngle = 12,
  flat = false,
}: Scroll3DSectionProps) {
  const ref = React.useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "center center"],
  });

  const rawRotateX = useTransform(
    scrollYProgress,
    [0, 0.7, 1],
    [entryAngle, 2, 0]
  );
  const rawOpacity = useTransform(scrollYProgress, [0, 0.25], [0, 1]);
  const rawY       = useTransform(scrollYProgress, [0, 1], [40, 0]);

  const rotateX = useSpring(rawRotateX, { stiffness: 60, damping: 20 });
  const opacity = useSpring(rawOpacity, { stiffness: 60, damping: 20 });
  const y       = useSpring(rawY,       { stiffness: 60, damping: 20 });

  if (flat) {
    return (
      <div ref={ref} className={className} style={style}>
        {children}
      </div>
    );
  }

  return (
    // The outer div is the perspective camera for this section
    <div
      ref={ref}
      className={className}
      style={{
        perspective: "1400px",
        perspectiveOrigin: "50% 30%",
        ...style,
      }}
    >
      <motion.div
        style={{
          rotateX,
          opacity,
          y,
          transformStyle: "preserve-3d",
          transformOrigin: "center top",
        }}
      >
        {children}
      </motion.div>
    </div>
  );
}

// ── ParallaxLayer ────────────────────────────────────────────
// Wrap an element in this to give it a z-depth parallax relative
// to the enclosing scroll container. Positive depth = closer.

interface ParallaxLayerProps {
  children: React.ReactNode;
  depth?: number; // translateZ pixels (positive = toward viewer)
  className?: string;
  style?: React.CSSProperties;
}

export function ParallaxLayer({
  children,
  depth = 0,
  className,
  style,
}: ParallaxLayerProps) {
  return (
    <div
      className={className}
      style={{
        transform: `translateZ(${depth}px)`,
        transformStyle: "preserve-3d",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
