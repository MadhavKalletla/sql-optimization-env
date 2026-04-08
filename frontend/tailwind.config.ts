import type { Config } from "tailwindcss";

// ⚠️ Tailwind v4 NOTE:
// Custom animations / keyframes have been moved to globals.css using @theme {}
// This file is kept for IDE support but Tailwind v4 reads config from CSS, not here.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
};

export default config;