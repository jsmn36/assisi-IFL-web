import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          'primary-bg': '#E8E4D9',
          'forest-green': '#3D6248',
          'sage-green': '#567556',
          'deep-green': '#3B5F47',
          'cream-white': '#FAF8F3',
          'warm-gray': '#595950',
          'charcoal': '#2C2C2C',
          'gold': '#C9A961',
          'mist-blue': '#B8C5C5',
          'error': '#A65C52',
        },
      },
      fontFamily: {
        heading: ['var(--font-cormorant)', 'serif'],
        body: ['var(--font-montserrat)', 'sans-serif'],
        tagline: ['var(--font-italiana)', 'serif'],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
export default config;
