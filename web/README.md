# Captain Raccoon: Stories from the Quiet Harbors

A live storytelling and world-building website for an original character, Captain Raccoon. Built with modern web technologies, this project features a single-page interactive journey with subtle animations and a "cinematic night-harbor adventure" aesthetic.

## Tech Stack

- **Framework**: [Next.js](https://nextjs.org/) (App Router)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **Icons**: [Lucide React](https://lucide.dev/)

## Project Structure

- `/src/app`: Next.js App Router setup (`layout.tsx`, `page.tsx`, `globals.css`)
- `/src/components/ui`: Reusable layout and UI components (`Button`, `Card`, `Section`, `Container`, `Heading`, `Navbar`)
- `/src/components/sections`: The major sections of the single-page application:
  - `HeroSection`
  - `CharacterSection`
  - `TimelineSection`
  - `MapSection`
  - `LiveEpisodeSection`
  - `ParticipationSection`
  - `GallerySection`
  - `FooterSection`
- `/src/lib/utils.ts`: Utility functions (e.g., Tailwind class merging)

## Getting Started

### Prerequisites

Ensure you have Node.js (v18.17+) and npm installed.

### Installation

Clone the repository and install dependencies:

```bash
npm install
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Production Build

To build the application for production, run:

```bash
npm run build
```

Then, you can start the production server:

```bash
npm start
```

## Features

- **Responsive Design**: Built mobile-first to ensure it works on all screen sizes.
- **Scroll Animations**: Uses Framer Motion to reveal content smoothly as you scroll.
- **Interactive Timeline & Map**: Scrollytelling elements to explore the world.
- **Brand Colors**: Deep Navy, Teal, Amber/Gold, and Off-White predefined in Tailwind v4 `globals.css`.

## License
MIT
