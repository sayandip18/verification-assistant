import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14261c",
        forest: "#1f5c3a",
        paper: "#f4f1e8",
      },
    },
  },
  plugins: [],
};

export default config;
