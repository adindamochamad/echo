import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#0F172A",
          mid: "#1E293B",
          light: "#334155",
          deep: "#020818",
        },
        amber: {
          DEFAULT: "#F59E0B",
        },
        critical: { DEFAULT: "#EF4444", bg: "#FEF2F2" },
        warning: { DEFAULT: "#F59E0B", bg: "#FFFBEB" },
        good: { DEFAULT: "#22C55E", bg: "#F0FDF4" },
        info: { DEFAULT: "#3B82F6", bg: "#EFF6FF" },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(15,23,42,0.06), 0 8px 24px rgba(15,23,42,0.04)",
        "card-hover": "0 4px 12px rgba(15,23,42,0.10), 0 20px 48px rgba(15,23,42,0.08)",
        glow: "0 0 0 1px rgba(239,68,68,0.15), 0 8px 40px rgba(239,68,68,0.18)",
        "glow-amber": "0 0 40px rgba(245,158,11,0.3), 0 0 80px rgba(245,158,11,0.1)",
        "glow-blue": "0 0 40px rgba(59,130,246,0.2), 0 0 80px rgba(59,130,246,0.08)",
        "inner-glow": "inset 0 1px 0 rgba(255,255,255,0.1)",
        glass: "0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.08)",
      },
      animation: {
        "fade-up": "fadeUp 0.7s cubic-bezier(0.22,1,0.36,1) forwards",
        "fade-up-slow": "fadeUp 1s cubic-bezier(0.22,1,0.36,1) forwards",
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "slide-in-right": "slideInRight 0.6s cubic-bezier(0.22,1,0.36,1) forwards",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "glow-pulse": "glowPulse 2.5s ease-in-out infinite",
        "float": "float 6s ease-in-out infinite",
        "shimmer": "shimmer 2.5s linear infinite",
        "border-glow": "borderGlow 3s ease-in-out infinite",
        "count-up": "fadeIn 0.8s ease-out forwards",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(24px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(245,158,11,0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(245,158,11,0.6), 0 0 60px rgba(245,158,11,0.2)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        borderGlow: {
          "0%, 100%": { borderColor: "rgba(239,68,68,0.4)" },
          "50%": { borderColor: "rgba(239,68,68,0.9)" },
        },
      },
      opacity: {
        "3": "0.03",
        "4": "0.04",
        "6": "0.06",
        "7": "0.07",
        "8": "0.08",
        "12": "0.12",
        "15": "0.15",
        "18": "0.18",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "noise": "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
};

export default config;
