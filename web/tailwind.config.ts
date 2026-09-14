import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        kpu: {
          red: "#700D0A",
          redDark: "#4A0806",
          redLight: "#8F110D",
          gold: "#D4AF37",
          goldLight: "#F3E5AB",
        },
      },
    },
  },
  plugins: [],
};
export default config;
