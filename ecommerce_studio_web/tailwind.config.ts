import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#09090b",
        surface: "#18181b",
        elevated: "#27272a",
        border: "rgba(255, 255, 255, 0.08)",
        ring: "rgba(56, 189, 248, 0.5)",
        studio: {
          accent: "#0ea5e9",
          copilot: "#6366f1",
          success: "#10b981",
          warning: "#f59e0b",
          danger: "#f43f5e",
        },
      },
      animation: {
        shimmer: "shimmer 2s infinite linear",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
