/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        app: {
          bg: "#FAFAFF",
          bg2: "#F6F3FF",
          surface: "#FFFFFF",
          surface2: "#F4F1FF",
          text: "#1F2937",
          text2: "#4B5563",
          muted: "#9CA3AF",
          border: "#E5E7EB",
          accent: "#8B5CF6",
          accent2: "#A78BFA",
          accent3: "#C4B5FD",
          success: "#22C55E",
          warning: "#F59E0B",
          error: "#EF4444",
        },
        brand: {
          primary: "#6D28D9",
          accent: "#A78BFA",
          warning: "#F4A261",
          danger: "#E76F51",
        },
      },
    },
  },
  plugins: [],
};

