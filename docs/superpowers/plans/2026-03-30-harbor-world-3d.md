# Harbor World 3D Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all static Next.js sections with a fullscreen R3F WebGL harbor world where the camera flies through 8 procedural 3D stations as the user scrolls.

**Architecture:** Drei `ScrollControls` owns the scroll. A `CatmullRomCurve3` spline drives the camera through 8 keypoints. All geometry is procedural Three.js primitives. Text and UI overlaid via Drei `<Html>`. `HarborWorld` is dynamically imported with `{ ssr: false }` because WebGL requires browser APIs.

**Tech Stack:** `three`, `@react-three/fiber`, `@react-three/drei`, `@types/three`, Next.js 16.2 App Router, TypeScript, Tailwind CSS v4, Vitest

---

## File Map

### New files

| File | Responsibility |
|------|---------------|
| `src/components/three/HarborWorld.tsx` | Canvas + ScrollControls root. Dynamically imported by page.tsx. |
| `src/components/three/HarborScene.tsx` | Composes CameraRig + Harbor + Starfield + Fog + all Stations |
| `src/components/three/CameraRig.tsx` | Reads `scroll.offset`, moves camera along spline each frame |
| `src/components/three/camera-keypoints.ts` | Exported position + target arrays for the 8 stations |
| `src/components/three/Harbor.tsx` | Water plane, dock, warehouses, lampposts, PointLights |
| `src/components/three/WarpStarfield3D.tsx` | `Points` based starfield; speed driven by scroll offset |
| `src/components/three/FogParticles.tsx` | `InstancedMesh` fog puffs, count from `useResponsive3D` |
| `src/components/three/stations/Station0_Hero.tsx` | Html overlay: title, HUD, CTAs |
| `src/components/three/stations/Station1_Character.tsx` | Raccoon silhouette primitives + Html character card |
| `src/components/three/stations/Station2_Timeline.tsx` | Episode panels on warehouse walls + Html episode cards |
| `src/components/three/stations/Station3_Map.tsx` | Grid + location pins + Html labels |
| `src/components/three/stations/Station4_Live.tsx` | Monitor mesh (GLSL noise) + red beacon + Html player |
| `src/components/three/stations/Station5_Participation.tsx` | Torus portal + orbiting panels + Html CTAs |
| `src/components/three/stations/Station6_Gallery.tsx` | Arc of frame meshes + Html captions |
| `src/components/three/stations/Station7_Footer.tsx` | Html footer links (minimal — camera is rising out) |
| `src/lib/use-responsive-3d.ts` | Hook: isMobile → starCount, fogCount, fov, postProcessing |

### Modified files

| File | Change |
|------|--------|
| `src/app/page.tsx` | Replace all section imports with `dynamic(() => import('../components/three/HarborWorld'), { ssr: false })` |
| `package.json` | Add `three`, `@react-three/fiber`, `@react-three/drei`; add dev dep `@types/three` |

### Retired files (delete after Task 16)

```
src/components/ui/Scroll3DSection.tsx
src/components/ui/CarouselPerspective.tsx
src/components/ui/WarpStarfield.tsx
src/components/sections/HeroSection.tsx
src/components/sections/CharacterSection.tsx
src/components/sections/TimelineSection.tsx
src/components/sections/MapSection.tsx
src/components/sections/LiveEpisodeSection.tsx
src/components/sections/ParticipationSection.tsx
src/components/sections/GallerySection.tsx
src/components/sections/FooterSection.tsx
```

---

## Task 1: Install dependencies

**Files:**
- Modify: `web/package.json`

- [ ] **Step 1: Install runtime deps**

```bash
cd web
npm install three @react-three/fiber @react-three/drei
```

Expected: packages appear in `node_modules/`, `package.json` updated with `three`, `@react-three/fiber`, `@react-three/drei`.

- [ ] **Step 2: Install type definitions**

```bash
npm install -D @types/three
```

Expected: `@types/three` appears in `devDependencies`.

- [ ] **Step 3: Commit**

```bash
cd ..
git add web/package.json web/package-lock.json
git commit -m "chore: install three, r3f, drei, @types/three"
```

---

## Task 2: useResponsive3D hook

**Files:**
- Create: `web/src/lib/use-responsive-3d.ts`
- Test: `web/src/test/use-responsive-3d.test.ts`

- [ ] **Step 1: Write the failing test**

Create `web/src/test/use-responsive-3d.test.ts`:

```ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useResponsive3D } from '../lib/use-responsive-3d';

describe('useResponsive3D', () => {
  beforeEach(() => {
    vi.stubGlobal('innerWidth', 1440);
  });

  it('returns desktop config on wide viewport', () => {
    const { result } = renderHook(() => useResponsive3D());
    expect(result.current.isMobile).toBe(false);
    expect(result.current.starCount).toBe(2000);
    expect(result.current.fogCount).toBe(400);
    expect(result.current.cameraFov).toBe(60);
    expect(result.current.usePostProcessing).toBe(true);
    expect(result.current.geometryDetail).toBe('high');
  });

  it('returns mobile config on narrow viewport', () => {
    vi.stubGlobal('innerWidth', 375);
    const { result } = renderHook(() => useResponsive3D());
    expect(result.current.isMobile).toBe(true);
    expect(result.current.starCount).toBe(800);
    expect(result.current.fogCount).toBe(100);
    expect(result.current.cameraFov).toBe(75);
    expect(result.current.usePostProcessing).toBe(false);
    expect(result.current.geometryDetail).toBe('low');
  });

  it('updates when viewport resizes below 768px', () => {
    vi.stubGlobal('innerWidth', 1440);
    const { result } = renderHook(() => useResponsive3D());
    expect(result.current.isMobile).toBe(false);

    act(() => {
      vi.stubGlobal('innerWidth', 375);
      window.dispatchEvent(new Event('resize'));
    });

    expect(result.current.isMobile).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd web && npx vitest run src/test/use-responsive-3d.test.ts
```

Expected: FAIL — "Cannot find module '../lib/use-responsive-3d'"

- [ ] **Step 3: Create the hook**

Create `web/src/lib/use-responsive-3d.ts`:

```ts
import { useState, useEffect } from 'react';

export interface Responsive3DConfig {
  isMobile: boolean;
  starCount: number;
  fogCount: number;
  cameraFov: number;
  usePostProcessing: boolean;
  geometryDetail: 'low' | 'high';
}

const MOBILE_BREAKPOINT = 768;

function buildConfig(isMobile: boolean): Responsive3DConfig {
  return {
    isMobile,
    starCount: isMobile ? 800 : 2000,
    fogCount: isMobile ? 100 : 400,
    cameraFov: isMobile ? 75 : 60,
    usePostProcessing: !isMobile,
    geometryDetail: isMobile ? 'low' : 'high',
  };
}

export function useResponsive3D(): Responsive3DConfig {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  return buildConfig(isMobile);
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run src/test/use-responsive-3d.test.ts
```

Expected: PASS — 3 tests.

- [ ] **Step 5: Commit**

```bash
cd ..
git add web/src/lib/use-responsive-3d.ts web/src/test/use-responsive-3d.test.ts
git commit -m "feat: add useResponsive3D hook with mobile/desktop config"
```

---

## Task 3: Camera keypoints + CameraRig

**Files:**
- Create: `web/src/components/three/camera-keypoints.ts`
- Create: `web/src/components/three/CameraRig.tsx`
- Test: `web/src/test/camera-keypoints.test.ts`

- [ ] **Step 1: Write the failing test**

Create `web/src/test/camera-keypoints.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { CAMERA_POSITIONS, CAMERA_TARGETS } from '../components/three/camera-keypoints';

describe('camera-keypoints', () => {
  it('has exactly 8 position keypoints', () => {
    expect(CAMERA_POSITIONS).toHaveLength(8);
  });

  it('has exactly 8 target keypoints', () => {
    expect(CAMERA_TARGETS).toHaveLength(8);
  });

  it('each position is a [number, number, number] tuple', () => {
    for (const pos of CAMERA_POSITIONS) {
      expect(pos).toHaveLength(3);
      pos.forEach(n => expect(typeof n).toBe('number'));
    }
  });

  it('each target is a [number, number, number] tuple', () => {
    for (const tgt of CAMERA_TARGETS) {
      expect(tgt).toHaveLength(3);
      tgt.forEach(n => expect(typeof n).toBe('number'));
    }
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd web && npx vitest run src/test/camera-keypoints.test.ts
```

Expected: FAIL — "Cannot find module"

- [ ] **Step 3: Create camera keypoints**

Create `web/src/components/three/camera-keypoints.ts`:

```ts
// 8 camera positions — one per station (index = station number)
// Harbor coordinate space: Y=up, water at Y=0, dock at Z=5, X=0
export const CAMERA_POSITIONS: [number, number, number][] = [
  [0,   20,  30],  // 0: Hero — high above harbor, descending
  [-2,  2.5,  8],  // 1: Character — dock-level near lamppost
  [0,   4,   -5],  // 2: Timeline — entering warehouse alley
  [0,   35,   0],  // 3: Map — overhead tactical view
  [12,  3,  -10],  // 4: Live — inside warehouse facing monitor
  [0,   4,  -28],  // 5: Participation — open plaza
  [0,   5,  -40],  // 6: Gallery — along arc of frames
  [0,   45,  15],  // 7: Footer — rising high above, full harbor below
];

// Where camera looks at each station
export const CAMERA_TARGETS: [number, number, number][] = [
  [0,   0,    0],  // 0: Harbor center
  [0,   1,    4],  // 1: Raccoon figure on dock
  [0,   3,  -15],  // 2: Depth of alley
  [0,   0,    0],  // 3: Harbor from above
  [12,  3,  -18],  // 4: Monitor wall
  [0,   2,  -32],  // 5: Plaza center / torus portal
  [8,   5,  -40],  // 6: Gallery frame arc center
  [0,   0,    0],  // 7: Whole harbor from high above
];
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run src/test/camera-keypoints.test.ts
```

Expected: PASS — 4 tests.

- [ ] **Step 5: Create CameraRig component**

Create `web/src/components/three/CameraRig.tsx`:

```tsx
"use client";

import { useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { useScroll } from "@react-three/drei";
import { CatmullRomCurve3, Vector3 } from "three";
import { CAMERA_POSITIONS, CAMERA_TARGETS } from "./camera-keypoints";

const positionCurve = new CatmullRomCurve3(
  CAMERA_POSITIONS.map(([x, y, z]) => new Vector3(x, y, z))
);
const targetCurve = new CatmullRomCurve3(
  CAMERA_TARGETS.map(([x, y, z]) => new Vector3(x, y, z))
);

const _pos = new Vector3();
const _tgt = new Vector3();

export function CameraRig() {
  const { camera } = useThree();
  const scroll = useScroll();

  useFrame(() => {
    const t = scroll.offset;
    positionCurve.getPoint(t, _pos);
    targetCurve.getPoint(t, _tgt);
    camera.position.copy(_pos);
    camera.lookAt(_tgt);
  });

  return null;
}
```

- [ ] **Step 6: Commit**

```bash
cd ..
git add web/src/components/three/camera-keypoints.ts \
        web/src/components/three/CameraRig.tsx \
        web/src/test/camera-keypoints.test.ts
git commit -m "feat: add camera spline keypoints and CameraRig"
```

---

## Task 4: Harbor environment

**Files:**
- Create: `web/src/components/three/Harbor.tsx`

- [ ] **Step 1: Create Harbor component**

Create `web/src/components/three/Harbor.tsx`:

```tsx
"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Mesh, ShaderMaterial, Color } from "three";

// ── Water shader ─────────────────────────────────────────
const waterVertexShader = `
  uniform float uTime;
  varying vec2 vUv;
  void main() {
    vUv = uv;
    vec3 pos = position;
    pos.z += sin(pos.x * 0.5 + uTime * 0.6) * 0.3;
    pos.z += sin(pos.y * 0.4 + uTime * 0.9) * 0.2;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`;

const waterFragmentShader = `
  uniform vec3 uColor;
  varying vec2 vUv;
  void main() {
    float depth = vUv.y;
    vec3 col = mix(uColor * 0.4, uColor, depth);
    gl_FragColor = vec4(col, 1.0);
  }
`;

function Water() {
  const matRef = useRef<ShaderMaterial>(null!);

  useFrame(({ clock }) => {
    if (matRef.current) matRef.current.uniforms.uTime.value = clock.elapsedTime;
  });

  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]}>
      <planeGeometry args={[120, 120, 32, 32]} />
      <shaderMaterial
        ref={matRef}
        vertexShader={waterVertexShader}
        fragmentShader={waterFragmentShader}
        uniforms={{
          uTime: { value: 0 },
          uColor: { value: new Color("#0d2235") },
        }}
      />
    </mesh>
  );
}

// ── Dock ─────────────────────────────────────────────────
function Dock() {
  return (
    <group position={[0, 0, 5]}>
      {/* Main dock platform */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[20, 0.6, 4]} />
        <meshStandardMaterial color="#3d2810" roughness={0.9} metalness={0.1} />
      </mesh>
      {/* Dock posts */}
      {[-8, -4, 0, 4, 8].map((x) => (
        <mesh key={x} position={[x, -1.5, 2]}>
          <cylinderGeometry args={[0.15, 0.2, 3, 6]} />
          <meshStandardMaterial color="#2a1e0e" roughness={1} />
        </mesh>
      ))}
      {/* Crates */}
      {[[-5, 0.7, -0.5], [5.5, 0.7, -0.5], [5.5, 1.7, -0.5], [-3.5, 0.7, 0.5]] .map(([x, y, z], i) => (
        <mesh key={i} position={[x, y, z]}>
          <boxGeometry args={[1.4, 1.4, 1.4]} />
          <meshStandardMaterial color="#2a1e0e" roughness={0.95} />
        </mesh>
      ))}
    </group>
  );
}

// ── Lamppost ─────────────────────────────────────────────
function Lamppost({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh>
        <cylinderGeometry args={[0.08, 0.12, 6, 6]} />
        <meshStandardMaterial color="#444" roughness={0.6} metalness={0.4} />
      </mesh>
      {/* Arm */}
      <mesh position={[0.5, 2.8, 0]} rotation={[0, 0, -Math.PI / 8]}>
        <cylinderGeometry args={[0.05, 0.05, 1.2, 5]} />
        <meshStandardMaterial color="#444" roughness={0.6} metalness={0.4} />
      </mesh>
      {/* Lamp globe */}
      <mesh position={[0.9, 2.6, 0]}>
        <sphereGeometry args={[0.18, 8, 8]} />
        <meshStandardMaterial color="#ffcc88" emissive="#ffaa44" emissiveIntensity={1.5} />
      </mesh>
      {/* Light */}
      <pointLight position={[0.9, 2.6, 0]} color="#ffcc66" intensity={8} distance={12} decay={2} />
    </group>
  );
}

// ── Warehouses ────────────────────────────────────────────
function Warehouse({ position, size }: { position: [number, number, number]; size: [number, number, number] }) {
  const [w, h, d] = size;
  return (
    <group position={position}>
      <mesh position={[0, h / 2, 0]}>
        <boxGeometry args={[w, h, d]} />
        <meshStandardMaterial color="#111827" roughness={0.95} metalness={0.05} />
      </mesh>
      {/* Windows — emissive slots */}
      {[-w / 4, w / 4].map((wx, i) =>
        [h * 0.3, h * 0.6].map((wy, j) => (
          <mesh key={`${i}-${j}`} position={[wx, wy, d / 2 + 0.05]}>
            <planeGeometry args={[1.2, 0.8]} />
            <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={0.25} transparent opacity={0.4} />
          </mesh>
        ))
      )}
    </group>
  );
}

// ── Harbor (composed) ────────────────────────────────────
export function Harbor() {
  return (
    <group>
      {/* Lighting */}
      <ambientLight color="#1a2a3a" intensity={0.6} />
      <directionalLight position={[10, 20, 10]} color="#aaccff" intensity={0.4} />

      <Water />
      <Dock />

      {/* Lampposts along dock */}
      <Lamppost position={[-6, 0, 5]} />
      <Lamppost position={[0, 0, 5]} />
      <Lamppost position={[6, 0, 5]} />

      {/* Warehouses */}
      <Warehouse position={[-18, 0, -5]} size={[12, 9, 20]} />
      <Warehouse position={[18, 0, -5]} size={[12, 9, 20]} />
      {/* Back warehouses (deeper alley) */}
      <Warehouse position={[-16, 0, -22]} size={[10, 8, 14]} />
      <Warehouse position={[16, 0, -22]} size={[10, 8, 14]} />
    </group>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/Harbor.tsx
git commit -m "feat: add procedural Harbor environment (water, dock, warehouses, lights)"
```

---

## Task 5: WarpStarfield3D

**Files:**
- Create: `web/src/components/three/WarpStarfield3D.tsx`

- [ ] **Step 1: Create WarpStarfield3D**

Create `web/src/components/three/WarpStarfield3D.tsx`:

```tsx
"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { useScroll } from "@react-three/drei";
import { BufferGeometry, Float32BufferAttribute, Points, PointsMaterial } from "three";

interface WarpStarfield3DProps {
  count: number; // pass from useResponsive3D
}

export function WarpStarfield3D({ count }: WarpStarfield3DProps) {
  const pointsRef = useRef<Points>(null!);
  const scroll = useScroll();

  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3]     = (Math.random() - 0.5) * 200; // x
      arr[i * 3 + 1] = (Math.random() - 0.5) * 200; // y
      arr[i * 3 + 2] = (Math.random() - 0.5) * 200; // z
    }
    return arr;
  }, [count]);

  useFrame((_, delta) => {
    if (!pointsRef.current) return;
    // Scroll near 0 = fast warp; scroll near 1 = slow drift
    const t = scroll.offset;
    const ease = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    const speed = 18 * (1 - ease) + 0.35 * ease;

    // Move all stars toward camera (negative Z = forward)
    const pos = pointsRef.current.geometry.attributes.position;
    for (let i = 0; i < count; i++) {
      (pos as Float32BufferAttribute).array[i * 3 + 2] += speed * delta * 10;
      // Wrap when too close
      if ((pos as Float32BufferAttribute).array[i * 3 + 2] > 100) {
        (pos as Float32BufferAttribute).array[i * 3 + 2] -= 200;
      }
    }
    pos.needsUpdate = true;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial color="#aaddff" size={0.15} sizeAttenuation transparent opacity={0.8} />
    </points>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/WarpStarfield3D.tsx
git commit -m "feat: add WarpStarfield3D with scroll-driven warp speed"
```

---

## Task 6: FogParticles

**Files:**
- Create: `web/src/components/three/FogParticles.tsx`

- [ ] **Step 1: Create FogParticles**

Create `web/src/components/three/FogParticles.tsx`:

```tsx
"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { InstancedMesh, Object3D, MeshStandardMaterial } from "three";

interface FogParticlesProps {
  count: number; // from useResponsive3D
}

const _dummy = new Object3D();

export function FogParticles({ count }: FogParticlesProps) {
  const meshRef = useRef<InstancedMesh>(null!);

  const data = useMemo(() => {
    return Array.from({ length: count }, () => ({
      x: (Math.random() - 0.5) * 40,
      y: Math.random() * 4,
      z: Math.random() * -40,
      speed: 0.02 + Math.random() * 0.04,
      scale: 1.5 + Math.random() * 3,
      phase: Math.random() * Math.PI * 2,
    }));
  }, [count]);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.elapsedTime;
    data.forEach((p, i) => {
      _dummy.position.set(
        p.x + Math.sin(t * p.speed + p.phase) * 2,
        p.y + Math.sin(t * p.speed * 0.5) * 0.3,
        p.z
      );
      _dummy.scale.setScalar(p.scale);
      _dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, _dummy.matrix);
    });
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, count]}>
      <sphereGeometry args={[0.5, 4, 4]} />
      <meshStandardMaterial color="#8ab0c0" transparent opacity={0.06} depthWrite={false} />
    </instancedMesh>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/FogParticles.tsx
git commit -m "feat: add instanced FogParticles component"
```

---

## Task 7: HarborWorld root + HarborScene wiring

**Files:**
- Create: `web/src/components/three/HarborScene.tsx`
- Create: `web/src/components/three/HarborWorld.tsx`

- [ ] **Step 1: Create HarborScene**

Create `web/src/components/three/HarborScene.tsx`:

```tsx
"use client";

import { Responsive3DConfig } from "@/lib/use-responsive-3d";
import { CameraRig } from "./CameraRig";
import { Harbor } from "./Harbor";
import { WarpStarfield3D } from "./WarpStarfield3D";
import { FogParticles } from "./FogParticles";
import { Station0_Hero } from "./stations/Station0_Hero";
import { Station1_Character } from "./stations/Station1_Character";
import { Station2_Timeline } from "./stations/Station2_Timeline";
import { Station3_Map } from "./stations/Station3_Map";
import { Station4_Live } from "./stations/Station4_Live";
import { Station5_Participation } from "./stations/Station5_Participation";
import { Station6_Gallery } from "./stations/Station6_Gallery";
import { Station7_Footer } from "./stations/Station7_Footer";

export function HarborScene({ config }: { config: Responsive3DConfig }) {
  const r = config;

  return (
    <>
      <CameraRig />
      <WarpStarfield3D count={r.starCount} />
      <FogParticles count={r.fogCount} />
      <Harbor />
      <Station0_Hero />
      <Station1_Character />
      <Station2_Timeline />
      <Station3_Map />
      <Station4_Live />
      <Station5_Participation />
      <Station6_Gallery />
      <Station7_Footer />
    </>
  );
}
```

- [ ] **Step 2: Create HarborWorld (Canvas root)**

Create `web/src/components/three/HarborWorld.tsx`:

```tsx
"use client";

import { Canvas } from "@react-three/fiber";
import { ScrollControls } from "@react-three/drei";
import { Navbar } from "@/components/ui/navbar";
import { HarborScene } from "./HarborScene";
import { useResponsive3D, Responsive3DConfig } from "@/lib/use-responsive-3d";

// HarborWorld reads responsive config once and passes it down,
// so HarborScene does NOT call useResponsive3D() again.
export function HarborWorld() {
  const config = useResponsive3D();

  return (
    <div className="relative w-full h-screen bg-doc-navy">
      {/* Navbar stays as fixed HTML overlay */}
      <Navbar />

      {/* Fullscreen WebGL canvas */}
      <Canvas
        camera={{ fov: config.cameraFov, near: 0.1, far: 500 }}
        gl={{
          antialias: true,
          powerPreference: "high-performance",
          alpha: false,
        }}
        style={{ position: "fixed", inset: 0, width: "100%", height: "100%" }}
        dpr={[1, 2]}
      >
        {/* pages = number of screen-heights of scroll space */}
        <ScrollControls pages={8} damping={0.15}>
          <HarborScene config={config} />
        </ScrollControls>
      </Canvas>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
cd ..
git add web/src/components/three/HarborScene.tsx \
        web/src/components/three/HarborWorld.tsx
git commit -m "feat: add HarborScene and HarborWorld Canvas root"
```

---

## Task 8: Station 0 — Hero

**Files:**
- Create: `web/src/components/three/stations/Station0_Hero.tsx`

- [ ] **Step 1: Create Station0_Hero**

Create `web/src/components/three/stations/Station0_Hero.tsx`:

```tsx
"use client";

import { Html, useScroll } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import { BoxGeometry, Group } from "three";

// Pre-create geometry outside component to avoid re-allocation per-render
const _panelEdgesGeo = new BoxGeometry(5, 3, 0.1);

export function Station0_Hero() {
  const groupRef = useRef<Group>(null!);
  const scroll = useScroll();

  useFrame(() => {
    if (!groupRef.current) return;
    // Fade out as user scrolls past station 0 (first 1/8 of scroll)
    const t = scroll.offset;
    groupRef.current.visible = t < 0.18;
  });

  return (
    <group ref={groupRef} position={[0, 2, 10]}>
      <Html
        center
        transform
        occlude={false}
        style={{ pointerEvents: "none", userSelect: "none" }}
      >
        <div className="text-center" style={{ width: "90vw", maxWidth: "900px" }}>
          {/* Massive title */}
          <h1
            className="font-display font-black uppercase leading-[0.75] tracking-tighter text-center"
            style={{ fontSize: "clamp(4rem, 15vw, 14rem)" }}
          >
            <span className="block text-zinc-100 mix-blend-overlay">Captain</span>
            <span className="block text-doc-paper opacity-80">Raccoon</span>
          </h1>
          {/* HUD crosshair */}
          <div className="relative flex items-center justify-center mt-8 opacity-30">
            <div className="w-32 h-32 border border-cyan-400 rounded-full" />
            <div className="absolute w-36 h-px bg-cyan-400" />
            <div className="absolute w-px h-36 bg-cyan-400" />
          </div>
          {/* CTAs */}
          <div className="flex gap-4 justify-center mt-10 pointer-events-auto">
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); window.scrollTo({ top: window.innerHeight, behavior: "smooth" }); }}
              className="px-6 py-3 bg-doc-paper text-doc-navy font-mono font-bold text-xs uppercase tracking-wider hover:bg-white transition-colors"
            >
              [Access Log]
            </a>
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); window.scrollTo({ top: window.innerHeight * 2, behavior: "smooth" }); }}
              className="px-6 py-3 border border-doc-paper/30 text-doc-paper font-mono text-xs uppercase tracking-wider hover:bg-doc-paper/10 transition-colors"
            >
              [View Profile]
            </a>
          </div>
        </div>
      </Html>
    </group>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/stations/Station0_Hero.tsx
git commit -m "feat: add Station0_Hero with 3D Html overlay"
```

---

## Task 9: Station 1 — Character

**Files:**
- Create: `web/src/components/three/stations/Station1_Character.tsx`

- [ ] **Step 1: Create Station1_Character**

Create `web/src/components/three/stations/Station1_Character.tsx`:

```tsx
"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html, useScroll } from "@react-three/drei";
import { Group } from "three";

function RaccoonSilhouette() {
  return (
    <group position={[0, 0, 4]}>
      {/* Body */}
      <mesh position={[0, 0.9, 0]}>
        <cylinderGeometry args={[0.28, 0.35, 1.2, 8]} />
        <meshStandardMaterial color="#111" roughness={1} />
      </mesh>
      {/* Head */}
      <mesh position={[0, 1.8, 0]}>
        <sphereGeometry args={[0.32, 10, 10]} />
        <meshStandardMaterial color="#111" roughness={1} />
      </mesh>
      {/* Ears */}
      <mesh position={[-0.18, 2.18, 0]}>
        <coneGeometry args={[0.1, 0.22, 6]} />
        <meshStandardMaterial color="#111" roughness={1} />
      </mesh>
      <mesh position={[0.18, 2.18, 0]}>
        <coneGeometry args={[0.1, 0.22, 6]} />
        <meshStandardMaterial color="#111" roughness={1} />
      </mesh>
      {/* Tail */}
      <mesh position={[-0.5, 0.4, -0.1]} rotation={[0, 0, Math.PI / 4]}>
        <cylinderGeometry args={[0.08, 0.14, 0.9, 6]} />
        <meshStandardMaterial color="#111" roughness={1} />
      </mesh>
    </group>
  );
}

export function Station1_Character() {
  const groupRef = useRef<Group>(null!);
  const scroll = useScroll();

  useFrame(() => {
    if (!groupRef.current) return;
    const t = scroll.offset;
    // Visible between station 0 and station 2 (roughly 1/8 to 2.5/8)
    groupRef.current.visible = t > 0.1 && t < 0.28;
  });

  return (
    <group ref={groupRef}>
      <RaccoonSilhouette />
      {/* Character card */}
      <Html position={[2.5, 2, 5]} transform occlude={false} style={{ pointerEvents: "none" }}>
        <div
          className="bg-doc-charcoal/90 border border-white/10 p-5 backdrop-blur-sm rounded-sm"
          style={{ width: "260px" }}
        >
          <div className="w-full h-0.5 bg-cyan-400/50 mb-3" />
          <p className="font-mono text-cyan-400 text-[10px] tracking-[0.2em] uppercase mb-2">
            // Subject: The Guardian
          </p>
          <p className="text-doc-paper text-sm leading-relaxed font-serif italic mb-4">
            "He's not a pirate. He's not looking for trouble. But the harbor has secrets."
          </p>
          <div className="flex gap-6">
            {[{ v: "03", l: "episodes" }, { v: "05", l: "locations" }, { v: "∞", l: "choices" }].map((s) => (
              <div key={s.l}>
                <p className="font-mono font-bold text-2xl text-doc-paper">{s.v}</p>
                <p className="font-mono text-cyan-400/60 text-[9px] tracking-widest uppercase">{s.l}</p>
              </div>
            ))}
          </div>
        </div>
      </Html>
    </group>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/stations/Station1_Character.tsx
git commit -m "feat: add Station1_Character with raccoon silhouette and profile card"
```

---

## Task 10: Station 2 — Timeline

**Files:**
- Create: `web/src/components/three/stations/Station2_Timeline.tsx`

- [ ] **Step 1: Create Station2_Timeline**

Create `web/src/components/three/stations/Station2_Timeline.tsx`:

```tsx
"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html, useScroll } from "@react-three/drei";
import { Group } from "three";

const EPISODES = [
  { num: "01", title: "The Night Watch", date: "2024-03", desc: "First contact at Pier 4." },
  { num: "02", title: "The Cargo", date: "2024-06", desc: "Something is missing from the docks." },
  { num: "03", title: "The Fog", date: "2024-09", desc: "The harbor hides more than fish." },
];

export function Station2_Timeline() {
  const groupRef = useRef<Group>(null!);
  const scroll = useScroll();

  useFrame(() => {
    if (!groupRef.current) return;
    const t = scroll.offset;
    groupRef.current.visible = t > 0.22 && t < 0.42;
  });

  return (
    <group ref={groupRef}>
      {EPISODES.map((ep, i) => {
        const xPos = i % 2 === 0 ? -10 : 10;
        const zPos = -8 - i * 5;
        return (
          <group key={ep.num} position={[xPos, 3, zPos]}>
            {/* Glowing panel mesh */}
            <mesh>
              <boxGeometry args={[5, 3, 0.1]} />
              <meshStandardMaterial
                color="#0d1117"
                emissive="#22d3ee"
                emissiveIntensity={0.08}
                roughness={0.9}
              />
            </mesh>
            {/* Edge glow lines */}
            <lineSegments>
              <edgesGeometry args={[_panelEdgesGeo]} />
              <lineBasicMaterial color="#22d3ee" transparent opacity={0.4} />
            </lineSegments>
            {/* Html episode card */}
            <Html center transform occlude={false} style={{ pointerEvents: "none" }}>
              <div className="text-center" style={{ width: "220px" }}>
                <p className="font-mono text-cyan-400/60 text-[9px] tracking-widest uppercase mb-1">
                  Episode {ep.num}
                </p>
                <p className="font-mono font-bold text-doc-paper text-sm mb-1">{ep.title}</p>
                <p className="font-mono text-zinc-500 text-[9px] mb-2">{ep.date}</p>
                <p className="text-zinc-400 text-xs leading-relaxed">{ep.desc}</p>
              </div>
            </Html>
          </group>
        );
      })}
    </group>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/stations/Station2_Timeline.tsx
git commit -m "feat: add Station2_Timeline with floating episode panels"
```

---

## Task 11: Station 3 — Map

**Files:**
- Create: `web/src/components/three/stations/Station3_Map.tsx`

- [ ] **Step 1: Create Station3_Map**

Create `web/src/components/three/stations/Station3_Map.tsx`:

```tsx
"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html, useScroll, Grid } from "@react-three/drei";
import { Group } from "three";

const LOCATIONS = [
  { pos: [0, 1, 5] as [number, number, number],   label: "Pier 4",      coord: "45.1°N 14.3°E" },
  { pos: [-8, 1, -5] as [number, number, number],  label: "Warehouse A", coord: "45.0°N 14.2°E" },
  { pos: [8, 1, -5] as [number, number, number],   label: "Warehouse B", coord: "45.1°N 14.4°E" },
  { pos: [18, 1, 8] as [number, number, number],   label: "Lighthouse",  coord: "45.2°N 14.5°E" },
  { pos: [0, 1, -28] as [number, number, number],  label: "The Square",  coord: "44.9°N 14.3°E" },
];

function LocationPin({ position, label, coord }: { position: [number, number, number]; label: string; coord: string }) {
  const meshRef = useRef<Group>(null!);
  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(clock.elapsedTime * 2) * 0.15;
    }
  });

  return (
    <group position={position}>
      <group ref={meshRef}>
        {/* Pin needle */}
        <mesh position={[0, -0.5, 0]}>
          <cylinderGeometry args={[0.05, 0.05, 1, 5]} />
          <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={0.5} />
        </mesh>
        {/* Pin head */}
        <mesh position={[0, 0.1, 0]}>
          <sphereGeometry args={[0.2, 8, 8]} />
          <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={1} />
        </mesh>
        {/* Pulse light */}
        <pointLight color="#22d3ee" intensity={4} distance={6} decay={2} />
      </group>
      {/* Label */}
      <Html position={[0.4, 0.5, 0]} transform occlude={false} style={{ pointerEvents: "none" }}>
        <div style={{ whiteSpace: "nowrap" }}>
          <p className="font-mono text-cyan-400 text-[10px] font-bold">{label}</p>
          <p className="font-mono text-zinc-500 text-[9px]">{coord}</p>
        </div>
      </Html>
    </group>
  );
}

export function Station3_Map() {
  const groupRef = useRef<Group>(null!);
  const scroll = useScroll();

  useFrame(() => {
    if (!groupRef.current) return;
    const t = scroll.offset;
    groupRef.current.visible = t > 0.35 && t < 0.55;
  });

  return (
    <group ref={groupRef}>
      {/* Holographic grid */}
      <Grid
        position={[0, 0.1, 0]}
        args={[60, 60]}
        cellSize={4}
        cellThickness={0.5}
        cellColor="#22d3ee"
        sectionSize={20}
        sectionThickness={1}
        sectionColor="#22d3ee"
        fadeDistance={80}
        fadeStrength={1}
        infiniteGrid={false}
      />
      {/* Location pins */}
      {LOCATIONS.map((loc) => (
        <LocationPin key={loc.label} position={loc.pos} label={loc.label} coord={loc.coord} />
      ))}
      {/* Header */}
      <Html position={[0, 5, 0]} center transform occlude={false} style={{ pointerEvents: "none" }}>
        <div className="text-center">
          <p className="font-mono text-cyan-400/60 text-[9px] tracking-widest uppercase mb-1">// Tactical Overview</p>
          <p className="font-mono font-bold text-doc-paper text-lg tracking-widest uppercase">Harbor Map</p>
        </div>
      </Html>
    </group>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/stations/Station3_Map.tsx
git commit -m "feat: add Station3_Map with holographic grid and pulsing location pins"
```

---

## Task 12: Station 4 — Live

**Files:**
- Create: `web/src/components/three/stations/Station4_Live.tsx`

- [ ] **Step 1: Create Station4_Live**

Create `web/src/components/three/stations/Station4_Live.tsx`:

```tsx
"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html, useScroll } from "@react-three/drei";
import { Group, ShaderMaterial } from "three";

const crtVertexShader = `
  void main() {
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const crtFragmentShader = `
  uniform float uTime;
  void main() {
    vec2 uv = gl_FragCoord.xy / vec2(400.0, 280.0);
    float noise = fract(sin(dot(uv + uTime * 0.07, vec2(12.9898, 78.233))) * 43758.5453);
    float scanline = mod(gl_FragCoord.y + uTime * 25.0, 4.0) < 2.0 ? 0.82 : 1.0;
    float vignette = smoothstep(0.0, 0.4, uv.x) * smoothstep(1.0, 0.6, uv.x)
                   * smoothstep(0.0, 0.3, uv.y) * smoothstep(1.0, 0.7, uv.y);
    float brightness = noise * 0.25 * scanline * vignette;
    gl_FragColor = vec4(vec3(brightness), 1.0);
  }
`;

export function Station4_Live() {
  const groupRef = useRef<Group>(null!);
  const matRef = useRef<ShaderMaterial>(null!);
  const beaconRef = useRef<Group>(null!);
  const scroll = useScroll();

  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    const t = scroll.offset;
    groupRef.current.visible = t > 0.48 && t < 0.65;

    if (matRef.current) matRef.current.uniforms.uTime.value = clock.elapsedTime;

    if (beaconRef.current) {
      const pulse = 0.5 + Math.sin(clock.elapsedTime * 4) * 0.5;
      beaconRef.current.scale.setScalar(0.8 + pulse * 0.4);
    }
  });

  return (
    <group ref={groupRef} position={[12, 3, -10]}>
      {/* Monitor frame */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[6, 4, 0.3]} />
        <meshStandardMaterial color="#111" roughness={0.8} metalness={0.3} />
      </mesh>
      {/* CRT screen */}
      <mesh position={[0, 0, 0.16]}>
        <boxGeometry args={[5.5, 3.5, 0.01]} />
        <shaderMaterial
          ref={matRef}
          vertexShader={crtVertexShader}
          fragmentShader={crtFragmentShader}
          uniforms={{ uTime: { value: 0 } }}
        />
      </mesh>
      {/* Red beacon */}
      <group ref={beaconRef} position={[2.5, 2.5, 0.5]}>
        <mesh>
          <sphereGeometry args={[0.15, 8, 8]} />
          <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={2} />
        </mesh>
        <pointLight color="#ef4444" intensity={6} distance={8} decay={2} />
      </group>
      {/* Html overlay */}
      <Html position={[0, -3, 0.5]} center transform occlude={false} style={{ pointerEvents: "none" }}>
        <div className="text-center" style={{ width: "320px" }}>
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="font-mono text-red-400 text-xs font-bold tracking-widest uppercase">Live Broadcast</span>
          </div>
          <p className="font-mono text-zinc-400 text-[10px] tracking-wider">
            Surveillance feed active — Pier 4 sector
          </p>
        </div>
      </Html>
    </group>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/stations/Station4_Live.tsx
git commit -m "feat: add Station4_Live with CRT shader monitor and pulsing beacon"
```

---

## Task 13: Station 5 — Participation

**Files:**
- Create: `web/src/components/three/stations/Station5_Participation.tsx`

- [ ] **Step 1: Create Station5_Participation**

Create `web/src/components/three/stations/Station5_Participation.tsx`:

```tsx
"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html, useScroll } from "@react-three/drei";
import { Group } from "three";

export function Station5_Participation() {
  const groupRef = useRef<Group>(null!);
  const torusRef = useRef<Group>(null!);
  const scroll = useScroll();

  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    const t = scroll.offset;
    groupRef.current.visible = t > 0.60 && t < 0.78;

    if (torusRef.current) {
      torusRef.current.rotation.z = clock.elapsedTime * 0.3;
      torusRef.current.rotation.x = Math.sin(clock.elapsedTime * 0.2) * 0.15;
    }
  });

  return (
    <group ref={groupRef} position={[0, 2, -28]}>
      {/* Portal torus ring */}
      <group ref={torusRef}>
        <mesh>
          <torusGeometry args={[3, 0.12, 10, 60]} />
          <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={0.8} />
        </mesh>
        <pointLight color="#22d3ee" intensity={10} distance={15} decay={2} />
      </group>

      {/* Orbiting action panels */}
      {[0, 1, 2, 3].map((i) => {
        const angle = (i / 4) * Math.PI * 2;
        const r = 5.5;
        return (
          <group key={i} position={[Math.cos(angle) * r, Math.sin(angle) * r * 0.4, Math.sin(angle) * r * 0.3]}>
            <mesh>
              <boxGeometry args={[2, 1.2, 0.05]} />
              <meshStandardMaterial color="#0d1117" emissive="#22d3ee" emissiveIntensity={0.1} roughness={0.9} />
            </mesh>
          </group>
        );
      })}

      {/* Html CTA */}
      <Html position={[0, -4.5, 0]} center transform occlude={false}>
        <div className="text-center" style={{ width: "320px" }}>
          <p className="font-mono text-cyan-400/60 text-[9px] tracking-widest uppercase mb-2">// Join the mission</p>
          <p className="font-display font-bold text-doc-paper text-2xl uppercase mb-4">Participate</p>
          <div className="flex gap-3 justify-center pointer-events-auto">
            <a href="#" className="px-5 py-2 bg-doc-paper text-doc-navy font-mono font-bold text-[10px] uppercase tracking-wider hover:bg-white transition-colors">
              [Join Now]
            </a>
            <a href="#" className="px-5 py-2 border border-doc-paper/30 text-doc-paper font-mono text-[10px] uppercase tracking-wider hover:bg-doc-paper/10 transition-colors">
              [Learn More]
            </a>
          </div>
        </div>
      </Html>
    </group>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/stations/Station5_Participation.tsx
git commit -m "feat: add Station5_Participation with torus portal and orbiting panels"
```

---

## Task 14: Station 6 — Gallery

**Files:**
- Create: `web/src/components/three/stations/Station6_Gallery.tsx`

- [ ] **Step 1: Create Station6_Gallery**

Create `web/src/components/three/stations/Station6_Gallery.tsx`:

```tsx
"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html, useScroll } from "@react-three/drei";
import { Group } from "three";

const FRAMES = [
  { title: "Harbor at Dusk",    subtitle: "Episode 01 — Pier 4" },
  { title: "The Cargo",         subtitle: "Episode 02 — Dock B" },
  { title: "Fog Season",        subtitle: "Episode 03 — Channel" },
  { title: "Night Recon",       subtitle: "Classified — Sector 7" },
  { title: "The Informant",     subtitle: "Episode 04 — Warehouse" },
  { title: "Under the Bridge",  subtitle: "Episode 04 — Canal" },
];

// Pre-compute stable tilt values outside component (not in render)
const FRAME_TILTS = [0.03, -0.02, 0.04, -0.03, 0.02, -0.04];

export function Station6_Gallery() {
  const groupRef = useRef<Group>(null!);
  const scroll = useScroll();

  useFrame(() => {
    if (!groupRef.current) return;
    const t = scroll.offset;
    groupRef.current.visible = t > 0.73 && t < 0.92;
  });

  return (
    <group ref={groupRef} position={[0, 4, -40]}>
      {FRAMES.map((frame, i) => {
        const angle = ((i - (FRAMES.length - 1) / 2) / FRAMES.length) * Math.PI * 0.7;
        const radius = 12;
        const x = Math.sin(angle) * radius;
        const z = -Math.cos(angle) * radius * 0.4;
        const rotY = -angle;
        const tilt = FRAME_TILTS[i];

        return (
          <group key={frame.title} position={[x, 0, z]} rotation={[tilt, rotY, tilt * 0.5]}>
            {/* Frame mesh */}
            <mesh>
              <boxGeometry args={[2.8, 3.6, 0.08]} />
              <meshStandardMaterial color="#0d1117" roughness={0.9} />
            </mesh>
            {/* Inner panel */}
            <mesh position={[0, 0, 0.05]}>
              <boxGeometry args={[2.4, 3.1, 0.02]} />
              <meshStandardMaterial color="#111827" emissive="#22d3ee" emissiveIntensity={0.06} roughness={0.95} />
            </mesh>
            {/* Edge glow — top bar */}
            <mesh position={[0, 1.85, 0.05]}>
              <boxGeometry args={[2.8, 0.04, 0.04]} />
              <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={1} />
            </mesh>
            {/* Caption */}
            <Html position={[0, -2.2, 0.1]} center transform occlude={false} style={{ pointerEvents: "none" }}>
              <div className="text-center" style={{ width: "180px" }}>
                <p className="font-mono font-bold text-doc-paper text-xs">{frame.title}</p>
                <p className="font-mono text-zinc-600 text-[9px] mt-0.5">{frame.subtitle}</p>
              </div>
            </Html>
          </group>
        );
      })}
    </group>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/stations/Station6_Gallery.tsx
git commit -m "feat: add Station6_Gallery with arc of floating frame meshes"
```

---

## Task 15: Station 7 — Footer

**Files:**
- Create: `web/src/components/three/stations/Station7_Footer.tsx`

- [ ] **Step 1: Create Station7_Footer**

Create `web/src/components/three/stations/Station7_Footer.tsx`:

```tsx
"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html, useScroll } from "@react-three/drei";
import { Group } from "three";

export function Station7_Footer() {
  const groupRef = useRef<Group>(null!);
  const scroll = useScroll();

  useFrame(() => {
    if (!groupRef.current) return;
    const t = scroll.offset;
    groupRef.current.visible = t > 0.88;
  });

  return (
    <group ref={groupRef} position={[0, 10, 10]}>
      <Html center transform occlude={false}>
        <div className="text-center" style={{ width: "400px" }}>
          <p className="font-mono text-zinc-600 text-[9px] tracking-widest uppercase mb-6">
            // End of transmission
          </p>
          <p className="font-display font-black uppercase text-4xl text-doc-paper/20 mb-8">
            Captain Raccoon
          </p>
          <div className="flex gap-8 justify-center mb-6 pointer-events-auto">
            {["Episodes", "Characters", "Map", "Community"].map((link) => (
              <a key={link} href="#" className="font-mono text-zinc-500 text-[10px] uppercase tracking-wider hover:text-doc-paper transition-colors">
                {link}
              </a>
            ))}
          </div>
          <div className="flex-1 h-px bg-white/10 mb-4 mx-8" />
          <p className="font-mono text-zinc-700 text-[9px]">
            © 2024 Captain Raccoon Project. All rights reserved.
          </p>
        </div>
      </Html>
    </group>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/src/components/three/stations/Station7_Footer.tsx
git commit -m "feat: add Station7_Footer with minimal Html overlay"
```

---

## Task 16: Wire page.tsx and retire old components

**Files:**
- Modify: `web/src/app/page.tsx`
- Delete: retired files listed in file map

- [ ] **Step 1: Update page.tsx**

Replace the entire contents of `web/src/app/page.tsx` with:

```tsx
import dynamic from "next/dynamic";

const HarborWorld = dynamic(
  () => import("@/components/three/HarborWorld").then((m) => m.HarborWorld),
  {
    ssr: false,
    loading: () => (
      <div
        className="fixed inset-0 bg-doc-navy flex items-center justify-center"
        aria-label="Loading harbor world"
      >
        <p className="font-mono text-cyan-400/60 text-xs tracking-widest uppercase animate-pulse">
          [initializing harbor...]
        </p>
      </div>
    ),
  }
);

export default function Home() {
  return <HarborWorld />;
}
```

- [ ] **Step 2: Delete retired components**

```bash
cd web
rm src/components/ui/Scroll3DSection.tsx
rm src/components/ui/CarouselPerspective.tsx
rm src/components/ui/WarpStarfield.tsx
rm src/components/sections/HeroSection.tsx
rm src/components/sections/CharacterSection.tsx
rm src/components/sections/TimelineSection.tsx
rm src/components/sections/MapSection.tsx
rm src/components/sections/LiveEpisodeSection.tsx
rm src/components/sections/ParticipationSection.tsx
rm src/components/sections/GallerySection.tsx
rm src/components/sections/FooterSection.tsx
```

- [ ] **Step 3: Verify the build compiles**

```bash
npm run build
```

Expected: Build completes without TypeScript errors. If Three.js type errors appear (e.g. `lineBasicMaterial` not recognized as JSX), add this to `src/types/three-fiber.d.ts`:

```ts
import { Object3DNode } from "@react-three/fiber";
import { LineBasicMaterial, LineSegments } from "three";

declare module "@react-three/fiber" {
  interface ThreeElements {
    lineSegments: Object3DNode<LineSegments, typeof LineSegments>;
    lineBasicMaterial: Object3DNode<LineBasicMaterial, typeof LineBasicMaterial>;
  }
}
```

- [ ] **Step 4: Run dev server and visually verify**

```bash
npm run dev
```

Open `http://localhost:3000`. Expected:
- Loading screen appears briefly ("initializing harbor...")
- 3D harbor world loads — stars warping, harbor visible below
- Scrolling moves camera through all 8 stations
- Text overlays appear and disappear at correct scroll positions
- Mobile viewport (resize to 375px) renders with fewer particles

- [ ] **Step 5: Run all tests**

```bash
npx vitest run
```

Expected: All tests pass (useResponsive3D + camera-keypoints).

- [ ] **Step 6: Final commit**

```bash
cd ..
git add web/src/app/page.tsx
git commit -m "feat: wire HarborWorld into page.tsx, retire old section components"
```
