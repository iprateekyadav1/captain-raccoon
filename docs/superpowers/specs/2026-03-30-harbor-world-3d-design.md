# Harbor World 3D — Design Spec

**Date:** 2026-03-30
**Project:** Captain Raccoon (`web/`)
**Status:** Approved

---

## Overview

Replace the existing static Next.js sections with a fully immersive WebGL 3D world built on React Three Fiber. The camera flies through a procedural harbor scene as the user scrolls. All content (text, titles, CTAs) is overlaid via Drei's `<Html>` component anchored in 3D space. No pre-made 3D models — everything is procedural geometry.

---

## Architecture

### Tech Stack Additions

```
@react-three/fiber   — React renderer for Three.js
@react-three/drei    — Helpers: ScrollControls, Html, Text, useProgress, etc.
three                — Core WebGL engine
```

Existing dependencies (`framer-motion`, `lenis`) are no longer used on the main page — scroll is fully owned by Drei `ScrollControls`. They stay in `package.json` (other pages may use them).

### Component Structure

```
app/page.tsx
└── <HarborWorld>              ← new root component, replaces all sections
    ├── <Canvas>               ← R3F fullscreen canvas
    │   ├── <ScrollControls>   ← Drei: maps scroll → 0..1 progress
    │   │   └── <HarborScene>  ← camera path + all 3D stations
    │   │       ├── <CameraRig>         ← moves camera along CatmullRomCurve3
    │   │       ├── <Harbor>            ← shared environment (water, dock, warehouses, fog)
    │   │       ├── <Station0_Hero>
    │   │       ├── <Station1_Character>
    │   │       ├── <Station2_Timeline>
    │   │       ├── <Station3_Map>
    │   │       ├── <Station4_Live>
    │   │       ├── <Station5_Participation>
    │   │       ├── <Station6_Gallery>
    │   │       └── <Station7_Footer>
    │   ├── <WarpStarfield3D>   ← existing starfield re-implemented in R3F (Points)
    │   ├── <FogParticles>      ← instanced mesh, 200-400 fog puffs
    │   └── <Lights>            ← ambient + point lights (lampposts, moonlight)
    └── <Navbar>                ← kept as HTML overlay (position: fixed)
```

### Scroll → Camera Mapping

Drei `ScrollControls` provides a `useScroll()` hook that returns `scroll.offset` (0–1). `CameraRig` reads this value every frame and positions + rotates the camera along a `CatmullRomCurve3` spline with 8 keypoints — one per station.

```ts
// Pseudocode
const curve = new CatmullRomCurve3([...8 keypoints]);
const lookAt = new CatmullRomCurve3([...8 look targets]);

useFrame(() => {
  const t = scroll.offset;
  camera.position.copy(curve.getPoint(t));
  camera.lookAt(lookAt.getPoint(t));
});
```

---

## 8 Stations

### Station 0 — Hero: Wide Harbor Reveal
- **Camera position:** High above water, looking down at 45°
- **Entry state:** Stars at full warp speed (Points animating fast)
- **Transition:** Stars slow to drift as camera descends toward dock
- **3D elements:** Water plane (PlaneGeometry + custom shader), dock geometry, lampposts
- **Html overlay:** Massive "CAPTAIN RACCOON" title, HUD crosshair, CTA buttons
- **Atmosphere:** Deep navy, cyan glow, film grain (CSS overlay kept)

### Station 1 — Character: The Pier at Night
- **Camera position:** Eye-level at dock edge, slight upward tilt
- **3D elements:** Raccoon silhouette (SphereGeometry head + CylinderGeometry body, dark material), lamppost with PointLight (amber), water ripple plane
- **Html overlay:** Character name, description card, stats
- **Atmosphere:** Warm amber lamplight contrasting cold water reflection

### Station 2 — Timeline: The Warehouse Alley
- **Camera position:** Moving through a corridor of tall BoxGeometry warehouses
- **3D elements:** 4–6 warehouse blocks left/right, fog particles dense between them, episode panels as PlaneGeometry with emissive edges
- **Html overlay:** Episode cards floating on each panel mesh position
- **Atmosphere:** Very dark, narrow, noir fog

### Station 3 — Map: Harbor Overhead
- **Camera position:** High overhead, tilted straight down
- **3D elements:** Full harbor layout visible (dock, warehouses, water), location pins (CylinderGeometry + SphereGeometry tip) with pulsing PointLight, holographic grid (GridHelper or custom line geometry)
- **Html overlay:** Location labels, coordinate readouts
- **Atmosphere:** Tactical/military, cyan grid lines

### Station 4 — Live: The Broadcast Room
- **Camera position:** Inside a dark warehouse room, facing a monitor wall
- **3D elements:** BoxGeometry monitor/screen with emissive material (animated static texture or shader), red pulsing beacon (SphereGeometry + PointLight), scan-line particle sheet
- **Html overlay:** "LIVE BROADCAST" text, episode player UI
- **Atmosphere:** Red accent, CRT static, very dark room

### Station 5 — Participation: The Open Plaza
- **Camera position:** Center of open area, slight upward tilt to stars
- **3D elements:** TorusGeometry portal ring (glowing, slowly rotating), 3–4 floating PlaneGeometry panels orbiting the ring, star field visible above
- **Html overlay:** Participation CTAs, community links
- **Atmosphere:** Open, airy, stars above, teal portal glow

### Station 6 — Gallery: The Floating Frames
- **Camera position:** Gliding along an arc of frames
- **3D elements:** 6–8 BoxGeometry frames in a gentle curved arc, emissive edge material, subtle random tilt per frame, depth-of-field blur (Drei `<DepthOfField>` post-processing) on desktop only
- **Html overlay:** Image titles, caption text
- **Atmosphere:** Gallery-like, clean, frames as negative space

### Station 7 — Footer: Zoom Out to Stars
- **Camera position:** Rising high above entire harbor, looking down
- **3D elements:** Full harbor scene visible small below, star warp resumes
- **Html overlay:** Footer links, credits, social icons
- **Atmosphere:** Full circle — ends where it began

---

## Procedural Geometry Inventory

| Element | Geometry | Notes |
|---------|----------|-------|
| Water plane | `PlaneGeometry` (large) | Sine-wave vertex displacement via `onBeforeCompile` shader hook |
| Dock | `BoxGeometry` × 3 | Brown material, slight roughness |
| Warehouse blocks | `BoxGeometry` × 6–8 | Dark, emissive window slots |
| Lampposts | `CylinderGeometry` + `SphereGeometry` | PointLight child |
| Raccoon body | `CylinderGeometry` + `SphereGeometry` | Dark flat material |
| Crates | `BoxGeometry` × 4–6 | Stacked near dock |
| Stars | `Points` (BufferGeometry) | 2000 pts, animates Z speed |
| Fog particles | `InstancedMesh` (SphereGeometry) | 200 mobile / 400 desktop |
| Location pins | `CylinderGeometry` + `SphereGeometry` | Pulsing PointLight |
| Portal ring | `TorusGeometry` | Emissive, rotating |
| Gallery frames | `BoxGeometry` (flat) | Emissive edge |
| Monitor/screen | `BoxGeometry` | Emissive material with animated GLSL noise (time uniform) |
| Holographic grid | `GridHelper` | Cyan, transparent |

---

## Responsive Behaviour

Detected via `window.innerWidth` inside a `useEffect` / `useMemo`, stored in a context.

| Feature | Mobile (< 768px) | Desktop (≥ 768px) |
|---------|-----------------|-------------------|
| Fog particles | 100 instances | 400 instances |
| Star count | 800 | 2000 |
| Post-processing | None | DepthOfField on Gallery station |
| Geometry detail | Low segments | High segments |
| Html font size | Larger (touch-friendly) | Normal |
| Camera FOV | 75° | 60° |

---

## Files to Create / Modify

### New files
```
web/src/components/three/HarborWorld.tsx       ← root Canvas + ScrollControls
web/src/components/three/HarborScene.tsx       ← CameraRig + Harbor env
web/src/components/three/CameraRig.tsx         ← spline camera movement
web/src/components/three/Harbor.tsx            ← water, dock, warehouses, lights
web/src/components/three/WarpStarfield3D.tsx   ← Points-based starfield
web/src/components/three/FogParticles.tsx      ← instanced fog
web/src/components/three/stations/Station0_Hero.tsx
web/src/components/three/stations/Station1_Character.tsx
web/src/components/three/stations/Station2_Timeline.tsx
web/src/components/three/stations/Station3_Map.tsx
web/src/components/three/stations/Station4_Live.tsx
web/src/components/three/stations/Station5_Participation.tsx
web/src/components/three/stations/Station6_Gallery.tsx
web/src/components/three/stations/Station7_Footer.tsx
web/src/lib/use-responsive-3d.ts               ← mobile/desktop detection hook
```

### Modified files
```
web/app/page.tsx          ← replace all sections with <HarborWorld>
web/package.json          ← add three, @react-three/fiber, @react-three/drei
```

### Deleted / retired
```
web/src/components/ui/Scroll3DSection.tsx      ← replaced by ScrollControls
web/src/components/ui/CarouselPerspective.tsx  ← replaced by CameraRig
web/src/components/ui/WarpStarfield.tsx        ← replaced by WarpStarfield3D
web/src/components/sections/*                  ← all replaced by Station components
```

---

## Dependencies to Install

```bash
npm install three @react-three/fiber @react-three/drei
npm install -D @types/three
```

---

## Out of Scope

- Loading/progress screen (can be added later with Drei `useProgress`)
- Audio
- Touch gesture controls beyond scroll
- Accessibility mode fallback (future)
