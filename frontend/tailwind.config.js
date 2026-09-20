/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // CareerOS brand palette
        navy: {
          DEFAULT: "#0B1F3A",
          light: "#13294B",
        },
        accent: {
          DEFAULT: "#2563EB",
          light: "#3B82F6",
        },
        surface: "#F8FAFC",
        border: "#E2E8F0",
        success: "#16A34A",
      },
    },
  },
  plugins: [],
};
