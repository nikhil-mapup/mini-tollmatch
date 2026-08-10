import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Grounded in the subject: highway signage green, toll-gantry amber,
        // and a brick red reserved for confirmed billing errors — not a
        // generic SaaS blue/purple palette.
        ink: "#14231C",
        paper: "#F6F5F2",
        gantry: {
          50: "#EAF2EE",
          100: "#D2E5DC",
          300: "#7FAE97",
          600: "#1B4D3E",
          700: "#153E32",
          800: "#102F27",
        },
        caution: {
          100: "#FBEBC7",
          500: "#E3A008",
          600: "#B8850A",
        },
        brick: {
          100: "#F3DCD5",
          500: "#A6402C",
          600: "#8E3524",
        },
        moss: {
          100: "#DCEEE3",
          500: "#3D8361",
          600: "#316B4F",
        },
        line: "#E4E2DD",
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        sans: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
