import type { Metadata } from "next";
import { Outfit, Inter } from "next/font/google";
import { ParticleBackground } from "@/components/ui/ParticleBackground";
import SmoothScroll from "@/components/ui/SmoothScroll";
import "./globals.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Captain Raccoon | Stories from the Quiet Harbors",
  description: "A live, evolving story world. Interactive particles follow your every move.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${outfit.variable} ${inter.variable} antialiased scroll-smooth`}
    >
      {/*
        Dark zinc-950 body.
        ParticleBackground (z-index 1) floats above it.
        <main> (z-index 2) holds all page content above dots.
      */}
      <body className="bg-[#09090b] text-zinc-100 min-h-screen">
        <SmoothScroll>
          <ParticleBackground />
          {children}
        </SmoothScroll>
      </body>
    </html>
  );
}
