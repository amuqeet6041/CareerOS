/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
  ],
  darkMode: ["class"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "Geist",
          "Manrope",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          '"Segoe UI"',
          "Roboto",
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
      },
      colors: {
        // All brand tokens are CSS-variable driven so every component
        // inherits the active theme (light / dark) automatically.
        canvas: "rgb(var(--color-canvas) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        elevated: "rgb(var(--color-elevated) / <alpha-value>)",
        "elevated-strong": "rgb(var(--color-elevated-strong) / <alpha-value>)",
        navy: {
          DEFAULT: "rgb(var(--color-navy) / <alpha-value>)",
          light: "rgb(var(--color-navy-light) / <alpha-value>)",
        },
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        "ink-strong": "rgb(var(--color-ink-strong) / <alpha-value>)",
        "ink-muted": "rgb(var(--color-ink-muted) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        faint: "rgb(var(--color-faint) / <alpha-value>)",
        line: "rgb(var(--color-line) / <alpha-value>)",
        "line-subtle": "rgb(var(--color-line-subtle) / <alpha-value>)",
        accent: {
          DEFAULT: "rgb(var(--color-accent) / <alpha-value>)",
          light: "rgb(var(--color-accent-light) / <alpha-value>)",
        },
        gold: {
          DEFAULT: "rgb(var(--color-gold) / <alpha-value>)",
          bright: "rgb(var(--color-gold-bright) / <alpha-value>)",
          // gold.soft used as translucent fills via /opacity modifiers
        },
        primary: {
          DEFAULT: "rgb(var(--color-primary) / <alpha-value>)",
          bright: "rgb(var(--color-primary-bright) / <alpha-value>)",
        },
        success: "rgb(var(--color-success) / <alpha-value>)",
        warning: "rgb(var(--color-warning) / <alpha-value>)",
        danger: "rgb(var(--color-danger) / <alpha-value>)",
        info: "rgb(var(--color-info) / <alpha-value>)",
        violet: "rgb(var(--color-violet) / <alpha-value>)",
      },
      boxShadow: {
        card: "0 1px 2px rgb(15 26 48 / 0.05), 0 6px 20px rgb(15 26 48 / 0.05)",
        "card-hover":
          "0 1px 2px rgb(15 26 48 / 0.04), 0 10px 30px rgb(15 26 48 / 0.08)",
        "glow-primary": "0 8px 24px rgb(37 99 235 / 0.22)",
        "glow-gold": "0 8px 24px rgb(201 151 62 / 0.22)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(18px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          from: { backgroundPosition: "200% 0" },
          to: { backgroundPosition: "-200% 0" },
        },
        "pop-in": {
          "0%": { opacity: "0", transform: "scale(0.6)" },
          "60%": { opacity: "1", transform: "scale(1.06)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.75", transform: "scale(1.08)" },
        },
        "progress-grow": {
          from: { width: "0%" },
          to: { width: "100%" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(0.9)", opacity: "0.7" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease both",
        "fade-in-up": "fade-in-up 0.3s ease both",
        "scale-in": "scale-in 0.2s ease both",
        "slide-up": "slide-up 0.4s ease both",
        shimmer: "shimmer 1.8s linear infinite",
        "pop-in": "pop-in 0.45s cubic-bezier(0.16, 1, 0.3, 1) both",
        "pulse-soft": "pulse-soft 2.4s ease-in-out infinite",
        "progress-grow": "progress-grow 0.45s ease-out forwards",
        "pulse-ring": "pulse-ring 1.6s cubic-bezier(0.16, 1, 0.3, 1) infinite",
      },
    },
  },
  plugins: [],
};