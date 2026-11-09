import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#2563eb", hover: "#1d4ed8", dark: "#1e3a8a" },
        ink: "#0f172a",
        muted: "#64748b",
        canvas: "#f0f2f5",
        border: "#e2e8f0",
      },
      borderRadius: { card: "16px", control: "10px" },
      boxShadow: { soft: "0 12px 36px rgba(15, 23, 42, 0.08)" },
    },
  },
  plugins: [],
};

export default config;
