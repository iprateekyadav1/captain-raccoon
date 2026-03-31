export const tokens = {
  colors: {
    navy: "#0a0f18",
    navyLight: "#121926",
    olive: "#1e231e",
    oliveLight: "#2b332b",
    charcoal: "#111111",
    charcoalLight: "#1c1c1c",
    paper: "#e5e3db",
    ink: "#1a1918",
    cyan: "#22d3ee",
    cyanDim: "rgba(34, 211, 238, 0.15)",
    alert: "#ef4444",
  },
  typography: {
    display: "var(--font-outfit), sans-serif",
    sans: "var(--font-inter), sans-serif",
    mono: "'JetBrains Mono', 'SF Mono', 'Fira Mono', ui-monospace, monospace",
  },
  animations: {
    carousel: {
      perspective: 1200,
      rotateXBase: 15,
      zOffset: -200,
      duration: 0.8,
      ease: [0.16, 1, 0.3, 1],
    },
    background: {
      tiltStrength: 0.05,
      depthStrength: 0.1,
    }
  }
};
