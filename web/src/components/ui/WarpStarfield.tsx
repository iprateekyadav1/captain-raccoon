"use client";

import * as React from "react";
import { tokens } from "@/lib/design-tokens";

// ═══════════════════════════════════════════════
//  WARP STARFIELD — Pure Canvas 2D, zero deps
//  2000 stars in a 3D volume, projected to screen.
//  Scroll controls warp speed:
//    scrollY = 0         → speed 18 → warp streaks
//    scrollY = viewport  → speed 0.4 → gentle drift
// ═══════════════════════════════════════════════

const NUM_STARS = 2000;
const FOV       = 280;    // focal length (perspective strength)
const MAX_Z     = 1000;   // far-clip distance
const MIN_Z     = 1;      // near-clip
const SPREAD_X  = 900;    // x/y spread of the star field
const SPREAD_Y  = 600;

interface Star {
  x: number;  // 3D world position
  y: number;
  z: number;
  // projected screen pos from the PREVIOUS frame (for streaks)
  prevPx: number;
  prevPy: number;
  freshReset: boolean;  // skip streak-draw on the frame of reset
}

function makeStar(W: number, H: number, scatterZ = true): Star {
  return {
    x:        (Math.random() - 0.5) * SPREAD_X * 2,
    y:        (Math.random() - 0.5) * SPREAD_Y * 2,
    z:        scatterZ ? Math.random() * MAX_Z + 1 : MAX_Z,
    prevPx:   W / 2,
    prevPy:   H / 2,
    freshReset: !scatterZ,
  };
}

export interface WarpStarfieldProps {
  depth?: number; // 0 to 1
}

export function WarpStarfield({ depth = 0 }: WarpStarfieldProps) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);
  const speedRef  = React.useRef(18);  // mutable, read inside rAF
  const tiltRef   = React.useRef({ x: 0, y: 0, depth });

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const maybeCtx = canvas.getContext("2d");
    if (!maybeCtx) return;
    const ctx = maybeCtx; // const alias survives TS narrowing into closures

    let W = 0, H = 0;
    let rafId = 0;

    // ── Resize ─────────────────────────────────────────
    function resize() {
      const rect = canvas!.getBoundingClientRect();
      W = canvas!.width  = Math.round(rect.width);
      H = canvas!.height = Math.round(rect.height);
    }
    const resizeObs = new ResizeObserver(resize);
    resizeObs.observe(canvas);
    resize();

    // ── Star pool ────────────────────────────────────────
    // Scatter across the full z-range on init so the field fills immediately.
    let stars: Star[] = Array.from({ length: NUM_STARS }, () => makeStar(W, H, true));

    // ── Scroll → warp speed + tilt ────────────────────────
    function onScroll() {
      const scrollH  = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      const progress = Math.min(window.scrollY / (window.innerHeight * 0.8), 1);
      const fullProg = window.scrollY / scrollH; // 0→1 over full page

      // Ease the slowdown: easeInOutQuad
      const t = progress < 0.5
        ? 2 * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 2) / 2;
      // Lerp: warp (18) → slow drift (0.35)
      speedRef.current = 18 * (1 - t) + 0.35 * t;

      // Tilt driven by full-page scroll progress (-5° to +5°, -2° to +2°)
      tiltRef.current.x = (fullProg - 0.5) * 10;
      tiltRef.current.y = (fullProg - 0.5) * 4;
    }
    window.addEventListener("scroll", onScroll, { passive: true });

    // ── Animation loop ────────────────────────────────────
    function loop() {
      const speed = speedRef.current;
      const { x: tx, y: ty, depth: td } = tiltRef.current;
      const tiltXOffset = (tx / 180) * W;
      const tiltYOffset = (ty / 180) * H;
      const cx = W / 2 + tiltXOffset;
      const cy = H / 2 + tiltYOffset;

      // Semi-transparent clear:
      //   Fast (warp) → low alpha = long trails = streak effect
      //   Slow (drift) → high alpha = clean dots
      const clearAlpha = speed > 5
        ? 0.18 + (speed / 18) * 0.10   // warp: 0.18–0.28
        : 0.85 + ((5 - speed) / 5) * 0.10; // drift: 0.85–0.95
      ctx.fillStyle = `rgba(9,9,11,${clearAlpha.toFixed(2)})`;
      ctx.fillRect(0, 0, W, H);

      for (const s of stars) {
        // ── Compute new screen position ─────────────────
        // Apply depth shift to FOV for subtle scaling
        const perspective = (FOV * (1 + td * tokens.animations.background.depthStrength)) / s.z;
        const px = cx + s.x * perspective;
        const py = cy + s.y * perspective;

        // ── Move star toward camera ─────────────────────
        const oldPx = px;
        const oldPy = py;
        s.z -= speed;

        // ── Reset when too close ────────────────────────
        if (s.z <= MIN_Z) {
          Object.assign(s, makeStar(W, H, false));
          continue;
        }

        // ── Skip if off-screen ──────────────────────────
        const margin = 100;
        if (px < -margin || px > W + margin || py < -margin || py > H + margin) {
          s.prevPx = px;
          s.prevPy = py;
          continue;
        }

        // Depth 0=far, 1=near
        const depth     = Math.pow(1 - s.z / MAX_Z, 1.4);
        const alpha     = 0.08 + depth * 0.92;
        const coreSize  = 0.2 + depth * 2.4;

        if (speed > 2.5) {
          // ── WARP MODE: draw streaks ─────────────────
          // Streak from previous position to current
          const streakX = s.freshReset ? px : s.prevPx;
          const streakY = s.freshReset ? py : s.prevPy;

          ctx.beginPath();
          ctx.moveTo(streakX, streakY);
          ctx.lineTo(px, py);

          // Color: near = bright white, far = dim blue-white
          const r = Math.round(180 + depth * 75);
          const g = Math.round(210 + depth * 45);
          const b = 255;
          ctx.strokeStyle = `rgba(${r},${g},${b},${(alpha * 0.9).toFixed(2)})`;
          ctx.lineWidth   = coreSize * 0.55;
          ctx.lineCap     = "round";
          ctx.stroke();

        } else {
          // ── DRIFT MODE: glowing dots ────────────────
          // Outer glow
          const glowR = coreSize * 4;
          const grd   = ctx.createRadialGradient(px, py, 0, px, py, glowR);
          grd.addColorStop(0, `rgba(180,215,255,${(alpha * 0.35).toFixed(2)})`);
          grd.addColorStop(1, "rgba(9,9,11,0)");
          ctx.beginPath();
          ctx.arc(px, py, glowR, 0, Math.PI * 2);
          ctx.fillStyle = grd;
          ctx.fill();

          // Core dot
          ctx.beginPath();
          ctx.arc(px, py, coreSize, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(240,248,255,${alpha.toFixed(2)})`;
          ctx.fill();
        }

        s.prevPx    = oldPx;
        s.prevPy    = oldPy;
        s.freshReset = false;
      }

      rafId = requestAnimationFrame(loop);
    }

    loop();

    return () => {
      cancelAnimationFrame(rafId);
      resizeObs.disconnect();
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        zIndex: 0,
        display: "block",
        pointerEvents: "none",
      }}
    />
  );
}
