"use client";

import * as React from "react";

// ═══════════════════════════════════════════════════════
//  Antigravity Sprite Engine — RACCOON FACE EDITION
//  Replaces circles/squares/triangles with canvas-drawn
//  raccoon emoji faces (grey fur, black mask, pink nose).
//  Same upward-gravity + mouse-repulsion physics.
// ═══════════════════════════════════════════════════════

const NUM_PARTICLES = 45;
const GRAVITY       = -0.05;
const FRICTION      = 0.96;
const MOUSE_RADIUS  = 150;
const PUSH_STRENGTH = 4;
const MIN_SIZE      = 14;   // raccoon faces need a bit more room
const MAX_SIZE      = 36;

// Size classes so we have variety without rebuilding every tiny size
const SPRITE_SIZES  = [14, 20, 28, 36];

// Tint palette — subtle color cast on each raccoon face
const TINTS = [
  null,          // natural (no tint)
  "cyan",
  "amber",
  "rose",
  "violet",
  "emerald",
];

// ── Draw a cute raccoon face on an offscreen canvas ────────
function buildRaccoonSprite(size: number, tint: string | null, dpr: number): HTMLCanvasElement {
  const pad       = 10;
  const totalSize = size + pad * 2;

  const oc  = document.createElement("canvas");
  oc.width  = Math.round(totalSize * dpr);
  oc.height = Math.round(totalSize * dpr);
  const ox  = oc.getContext("2d")!;
  ox.setTransform(dpr, 0, 0, dpr, 0, 0);

  const cx = totalSize / 2;
  const cy = totalSize / 2;
  const r  = size / 2;

  // ── Drop shadow ──────────────────────────────────────
  ox.shadowColor   = "rgba(0,0,0,0.25)";
  ox.shadowBlur    = 8;
  ox.shadowOffsetX = 2;
  ox.shadowOffsetY = 3;

  // ── Main head — grey circle ──────────────────────────
  ox.beginPath();
  ox.arc(cx, cy, r, 0, Math.PI * 2);
  ox.fillStyle = tint === "cyan"    ? "#7ecfcf"
               : tint === "amber"   ? "#c8a06a"
               : tint === "rose"    ? "#c47a8a"
               : tint === "violet"  ? "#9a7ac8"
               : tint === "emerald" ? "#6aae84"
               : "#9ba3a8";   // natural grey
  ox.fill();

  // Turn off shadow for details
  ox.shadowColor = "transparent";

  // ── Lighter face centre ──────────────────────────────
  ox.beginPath();
  ox.ellipse(cx, cy + r * 0.15, r * 0.55, r * 0.5, 0, 0, Math.PI * 2);
  ox.fillStyle = tint ? "rgba(255,255,255,0.25)" : "#bfc5c9";
  ox.fill();

  // ── Ears (round bumps at top) ────────────────────────
  const earR    = r * 0.32;
  const earOffX = r * 0.62;
  const earOffY = r * 0.65;
  // Left
  ox.beginPath();
  ox.arc(cx - earOffX, cy - earOffY, earR, 0, Math.PI * 2);
  ox.fillStyle = tint === "cyan"    ? "#7ecfcf"
               : tint === "amber"   ? "#c8a06a"
               : tint === "rose"    ? "#c47a8a"
               : tint === "violet"  ? "#9a7ac8"
               : tint === "emerald" ? "#6aae84"
               : "#9ba3a8";
  ox.fill();
  // Inner left ear
  ox.beginPath();
  ox.arc(cx - earOffX, cy - earOffY, earR * 0.6, 0, Math.PI * 2);
  ox.fillStyle = "rgba(255,180,190,0.55)";
  ox.fill();
  // Right
  ox.beginPath();
  ox.arc(cx + earOffX, cy - earOffY, earR, 0, Math.PI * 2);
  ox.fillStyle = tint === "cyan"    ? "#7ecfcf"
               : tint === "amber"   ? "#c8a06a"
               : tint === "rose"    ? "#c47a8a"
               : tint === "violet"  ? "#9a7ac8"
               : tint === "emerald" ? "#6aae84"
               : "#9ba3a8";
  ox.fill();
  ox.beginPath();
  ox.arc(cx + earOffX, cy - earOffY, earR * 0.6, 0, Math.PI * 2);
  ox.fillStyle = "rgba(255,180,190,0.55)";
  ox.fill();

  // ── Black mask (raccoon eye patches) ─────────────────
  const maskY   = cy - r * 0.08;
  const patchW  = r * 0.40;
  const patchH  = r * 0.30;
  const patchGap = r * 0.14;
  // Left patch
  ox.beginPath();
  ox.ellipse(cx - patchGap - patchW * 0.5, maskY, patchW, patchH, -0.25, 0, Math.PI * 2);
  ox.fillStyle = "#1a1a1a";
  ox.fill();
  // Right patch
  ox.beginPath();
  ox.ellipse(cx + patchGap + patchW * 0.5, maskY, patchW, patchH, 0.25, 0, Math.PI * 2);
  ox.fillStyle = "#1a1a1a";
  ox.fill();

  // ── Eyes — white + dark pupils ───────────────────────
  const eyeR = r * 0.14;
  // Left eye
  ox.beginPath();
  ox.arc(cx - patchGap - patchW * 0.35, maskY, eyeR, 0, Math.PI * 2);
  ox.fillStyle = "#ffffff";
  ox.fill();
  ox.beginPath();
  ox.arc(cx - patchGap - patchW * 0.30, maskY + eyeR * 0.1, eyeR * 0.55, 0, Math.PI * 2);
  ox.fillStyle = "#111";
  ox.fill();
  // Eye shine left
  ox.beginPath();
  ox.arc(cx - patchGap - patchW * 0.22, maskY - eyeR * 0.35, eyeR * 0.22, 0, Math.PI * 2);
  ox.fillStyle = "rgba(255,255,255,0.8)";
  ox.fill();

  // Right eye
  ox.beginPath();
  ox.arc(cx + patchGap + patchW * 0.35, maskY, eyeR, 0, Math.PI * 2);
  ox.fillStyle = "#ffffff";
  ox.fill();
  ox.beginPath();
  ox.arc(cx + patchGap + patchW * 0.30, maskY + eyeR * 0.1, eyeR * 0.55, 0, Math.PI * 2);
  ox.fillStyle = "#111";
  ox.fill();
  // Eye shine right
  ox.beginPath();
  ox.arc(cx + patchGap + patchW * 0.48, maskY - eyeR * 0.35, eyeR * 0.22, 0, Math.PI * 2);
  ox.fillStyle = "rgba(255,255,255,0.8)";
  ox.fill();

  // ── Nose — dark oval ─────────────────────────────────
  const noseY = cy + r * 0.28;
  ox.beginPath();
  ox.ellipse(cx, noseY, r * 0.14, r * 0.10, 0, 0, Math.PI * 2);
  ox.fillStyle = "#2a2a2a";
  ox.fill();

  // ── Mouth — tiny smile ───────────────────────────────
  ox.beginPath();
  ox.moveTo(cx - r * 0.12, noseY + r * 0.12);
  ox.quadraticCurveTo(cx, noseY + r * 0.25, cx + r * 0.12, noseY + r * 0.12);
  ox.strokeStyle = "#333";
  ox.lineWidth   = Math.max(0.8, r * 0.04);
  ox.lineCap     = "round";
  ox.stroke();

  // ── Cheek blush ─────────────────────────────────────
  const blushY = cy + r * 0.18;
  const blushR = r * 0.18;
  ox.beginPath();
  ox.arc(cx - r * 0.5, blushY, blushR, 0, Math.PI * 2);
  ox.fillStyle = "rgba(255,120,120,0.3)";
  ox.fill();
  ox.beginPath();
  ox.arc(cx + r * 0.5, blushY, blushR, 0, Math.PI * 2);
  ox.fill();

  return oc;
}

// ── Sprite cache: sprites[size][tintIndex] = canvas ──────
type SpriteCache = Map<string, HTMLCanvasElement>;

function buildAllSprites(dpr: number): SpriteCache {
  const cache: SpriteCache = new Map();
  for (const size of SPRITE_SIZES) {
    for (let ti = 0; ti < TINTS.length; ti++) {
      cache.set(`${size}:${ti}`, buildRaccoonSprite(size, TINTS[ti], dpr));
    }
  }
  return cache;
}

// ── Particle struct ───────────────────────────────────────
interface Particle {
  x: number; y: number;
  vx: number; vy: number;
  size: number;          // display size (NOT sprite size)
  spriteSize: number;    // snapped to SPRITE_SIZES
  tintIndex: number;
  depth: number;
  angle: number;
  rotationSpeed: number;
}

function nearestSpriteSize(size: number): number {
  return SPRITE_SIZES.reduce((prev, curr) =>
    Math.abs(curr - size) < Math.abs(prev - size) ? curr : prev
  );
}

function makeParticle(W: number, H: number): Particle {
  const size = MIN_SIZE + Math.random() * (MAX_SIZE - MIN_SIZE);
  return {
    x:             Math.random() * W,
    y:             Math.random() * H,
    vx:            (Math.random() - 0.5) * 0.8,
    vy:            (Math.random() - 0.5) * 0.8,
    size,
    spriteSize:    nearestSpriteSize(size),
    tintIndex:     Math.floor(Math.random() * TINTS.length),
    depth:         0.5 + Math.random(),
    angle:         Math.random() * Math.PI * 2,
    rotationSpeed: (Math.random() - 0.5) * 0.03,
  };
}

// ── Component ─────────────────────────────────────────────
export function ParticleBackground() {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    let W = 0, H = 0, rafId = 0;
    let mx = -9999, my = -9999;

    function resize() {
      W = window.innerWidth;
      H = window.innerHeight;
      canvas!.width  = Math.round(W * dpr);
      canvas!.height = Math.round(H * dpr);
      canvas!.style.width  = W + "px";
      canvas!.style.height = H + "px";
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    let sprites = buildAllSprites(dpr);

    resize();

    const particles: Particle[] = Array.from({ length: NUM_PARTICLES }, () => makeParticle(W, H));

    function onMouse(e: MouseEvent)  { mx = e.clientX; my = e.clientY; }
    function onLeave()               { mx = -9999;      my = -9999;     }
    function onTouch(e: TouchEvent)  { mx = e.touches[0].clientX; my = e.touches[0].clientY; }
    function onTouchEnd()            { mx = -9999;      my = -9999;     }

    function onResize() { resize(); sprites = buildAllSprites(dpr); }

    window.addEventListener("mousemove",  onMouse,   { passive: true });
    window.addEventListener("mouseleave", onLeave);
    window.addEventListener("touchmove",  onTouch,   { passive: true });
    window.addEventListener("touchend",   onTouchEnd);
    window.addEventListener("resize",     onResize,  { passive: true });

    function loop() {
      ctx!.clearRect(0, 0, W, H);

      for (const p of particles) {
        // Anti-gravity
        p.vy += GRAVITY * 0.05 * p.depth;

        // Mouse repulsion
        const dx = p.x - mx, dy = p.y - my;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MOUSE_RADIUS && dist > 0.5) {
          const force = (MOUSE_RADIUS - dist) / MOUSE_RADIUS;
          const angle = Math.atan2(dy, dx);
          p.vx += Math.cos(angle) * force * PUSH_STRENGTH;
          p.vy += Math.sin(angle) * force * PUSH_STRENGTH;
        }

        // Friction
        p.vx *= FRICTION;
        p.vy *= FRICTION;

        // Move + rotate
        p.x    += p.vx;
        p.y    += p.vy;
        p.angle += p.rotationSpeed;

        // Edge handling — respawn at bottom when floated off top
        const m = p.size * 2;
        if (p.y < -m) {
          p.y  = H + m;
          p.x  = Math.random() * W;
          p.vx = (Math.random() - 0.5) * 0.8;
          p.vy = -Math.random() * 0.3;
          continue;
        }
        if (p.y > H + m) p.y = H + m;
        if (p.x < -m)    p.x = W + m;
        if (p.x > W + m) p.x = -m;

        // Draw via sprite cache
        const sprite = sprites.get(`${p.spriteSize}:${p.tintIndex}`);
        if (!sprite) continue;

        const displaySize = p.size * p.depth;
        // Sprite canvas totalSize = spriteSize + 2*pad = spriteSize + 20
        const spriteTotal = p.spriteSize + 20;
        const scale       = displaySize / p.spriteSize;
        const drawW       = spriteTotal * scale;
        const drawH       = spriteTotal * scale;

        ctx!.save();
        ctx!.translate(p.x, p.y);
        ctx!.rotate(p.angle);
        ctx!.globalAlpha = 0.88;
        ctx!.drawImage(sprite, -drawW / 2, -drawH / 2, drawW, drawH);
        ctx!.globalAlpha = 1;
        ctx!.restore();
      }

      rafId = requestAnimationFrame(loop);
    }

    loop();

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("mousemove",  onMouse);
      window.removeEventListener("mouseleave", onLeave);
      window.removeEventListener("touchmove",  onTouch);
      window.removeEventListener("touchend",   onTouchEnd);
      window.removeEventListener("resize",     onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: "fixed",
        top: 0, left: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 1,
        pointerEvents: "none",
        display: "block",
        willChange: "transform",
      }}
    />
  );
}
