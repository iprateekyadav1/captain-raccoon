"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform, useSpring } from "framer-motion";
import { withBasePath } from "@/lib/asset-path";

interface FloatingAssetProps {
  src: string;
  alt: string;
  className?: string;
  speed?: number; // Higher = slower relative to scroll
  rotateSpeed?: number;
  direction?: 'up' | 'down';
}

export default function FloatingAsset({ 
  src, 
  alt, 
  className, 
  speed = 0.5, 
  rotateSpeed = 50, 
  direction = 'up' 
}: FloatingAssetProps) {
  const ref = useRef<HTMLDivElement>(null);
  
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"]
  });

  const springConfig = { stiffness: 100, damping: 30, restDelta: 0.001 };
  
  const yRange = direction === 'up' ? [100 * speed, -100 * speed] : [-100 * speed, 100 * speed];
  const y = useSpring(useTransform(scrollYProgress, [0, 1], yRange), springConfig);
  const rotate = useSpring(useTransform(scrollYProgress, [0, 1], [0, rotateSpeed]), springConfig);

  return (
    <motion.div
      ref={ref}
      style={{ y, rotate }}
      className={`absolute pointer-events-none z-10 ${className}`}
    >
      <img
        src={withBasePath(src)}
        alt={alt}
        loading="lazy"
        decoding="async"
        className="w-full h-full object-contain drop-shadow-2xl"
      />
    </motion.div>
  );
}
