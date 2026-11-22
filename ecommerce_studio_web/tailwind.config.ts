import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        surface: {
          DEFAULT: "var(--surface)",
          hover: "var(--surface-hover)",
          active: "var(--surface-active)",
        },
        elevated: "var(--elevated)",
        inset: "var(--inset)",
        border: "var(--border)",
        "border-subtle": "var(--border-subtle)",
        "border-strong": "var(--border-strong)",
        ring: "var(--ring)",
        studio: {
          primary: {
            DEFAULT: "var(--studio-primary)",
            hover: "var(--studio-primary-hover)",
            light: "var(--studio-primary-light)",
          },
          accent: {
            DEFAULT: "var(--studio-accent)",
            hover: "var(--studio-accent-hover)",
            light: "var(--studio-accent-light)",
          },
          copilot: {
            DEFAULT: "var(--studio-copilot)",
            light: "var(--studio-copilot-light)",
          },
          success: {
            DEFAULT: "var(--studio-success)",
            bg: "var(--studio-success-bg)",
          },
          warning: {
            DEFAULT: "var(--studio-warning)",
            bg: "var(--studio-warning-bg)",
          },
          danger: {
            DEFAULT: "var(--studio-danger)",
            bg: "var(--studio-danger-bg)",
          },
        },
        commerce: {
          text: {
            main: "var(--text-main)",
            body: "var(--text-body)",
            muted: "var(--text-muted)",
            subtle: "var(--text-subtle)",
          },
        },
      },
      boxShadow: {
        card: "var(--shadow-card)",
        "card-hover": "var(--shadow-card-hover)",
        popover: "var(--shadow-popover)",
      },
      animation: {
        shimmer: "studio-shimmer-light 1.8s ease-in-out infinite",
      },
      keyframes: {
        "studio-shimmer-light": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
