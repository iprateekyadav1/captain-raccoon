"use client";

import { Navbar } from "@/components/ui/navbar";
import { HeroSection } from "@/components/sections/HeroSection";
import { CharacterSection } from "@/components/sections/CharacterSection";
import { TimelineSection } from "@/components/sections/TimelineSection";
import { MapSection } from "@/components/sections/MapSection";
import { LiveEpisodeSection } from "@/components/sections/LiveEpisodeSection";
import { ParticipationSection } from "@/components/sections/ParticipationSection";
import { GallerySection } from "@/components/sections/GallerySection";
import { Footer } from "@/components/sections/FooterSection";
import { CarouselPerspective } from "@/components/ui/CarouselPerspective";
import { WarpStarfield } from "@/components/ui/WarpStarfield";
import { Scroll3DSection } from "@/components/ui/Scroll3DSection";

export default function Home() {
  return (
    <div className="relative bg-doc-navy">
      {/* ── Layer 0: Fixed warp starfield — self-manages tilt from scroll ── */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <WarpStarfield depth={0.5} />
      </div>

      {/* ── Navbar: fixed above everything ── */}
      <Navbar />

      {/* ── Global camera: subtle perspective tilt as you scroll ── */}
      <CarouselPerspective>

        {/* Hero gets no 3D reveal — it IS the opening frame */}
        <HeroSection />

        {/* Every subsequent section rotates into view from perspective */}
        <Scroll3DSection entryAngle={14}>
          <CharacterSection />
        </Scroll3DSection>

        <Scroll3DSection entryAngle={10}>
          <TimelineSection />
        </Scroll3DSection>

        <Scroll3DSection entryAngle={12}>
          <MapSection />
        </Scroll3DSection>

        <Scroll3DSection entryAngle={8}>
          <LiveEpisodeSection />
        </Scroll3DSection>

        <Scroll3DSection entryAngle={10}>
          <ParticipationSection />
        </Scroll3DSection>

        <Scroll3DSection entryAngle={8}>
          <GallerySection />
        </Scroll3DSection>

        <Scroll3DSection flat>
          <Footer />
        </Scroll3DSection>

      </CarouselPerspective>
    </div>
  );
}
