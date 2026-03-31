import { useScroll, useTransform, useSpring } from "framer-motion";
import { tokens } from "@/lib/design-tokens";

export function useCarouselScroll() {
  const { scrollYProgress } = useScroll();

  // 1. Z-Depth: "Inside the screen" effect
  // - Close at start
  // - Pushes back slightly during intermediate scrolls
  const rawZ = useTransform(
    scrollYProgress,
    [0, 0.1, 0.9, 1],
    [0, tokens.animations.carousel.zOffset, tokens.animations.carousel.zOffset, 0]
  );
  const z = useSpring(rawZ, { stiffness: 100, damping: 30 });

  // 2. RotateX: "Flipping" like a dossier
  // - Starts tilted
  // - Flattens as we scroll to section peaks
  const rawRotateX = useTransform(
    scrollYProgress,
    [0, 0.5, 1],
    [tokens.animations.carousel.rotateXBase, 0, -tokens.animations.carousel.rotateXBase]
  );
  const rotateX = useSpring(rawRotateX, { stiffness: 100, damping: 30 });

  // 3. Shifting Background (Stars)
  // - Slight perspective tilt for the starfield
  const rawBgTiltX = useTransform(scrollYProgress, [0, 1], [-5, 5]);
  const rawBgTiltY = useTransform(scrollYProgress, [0, 1], [-2, 2]);
  const bgTiltX = useSpring(rawBgTiltX, { stiffness: 50, damping: 20 });
  const bgTiltY = useSpring(rawBgTiltY, { stiffness: 50, damping: 20 });

  return {
    z,
    rotateX,
    background: {
      tiltX: bgTiltX,
      tiltY: bgTiltY,
    },
    scrollYProgress,
  };
}
