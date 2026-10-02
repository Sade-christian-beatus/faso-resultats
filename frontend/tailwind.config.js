// Tailwind build config (decision of 2026-10-02: pre-built CSS instead of the CDN
// script, see docs/ARCHITECTURE.md § Frontend). Brand tokens: docs/CHARTE_GRAPHIQUE.md.
// "faso" is a full shade scale built around the official green #00A651 (= faso-500):
// white text on faso-500 is below WCAG AA, so buttons and text use faso-700+.
//
// Classes are found by scanning the HTML and JS below: always write them as complete
// literal strings in the code ("bg-red-700", never `bg-${couleur}-700`), otherwise they
// are missing from the generated CSS.
module.exports = {
  content: ["./public/**/*.html", "./public/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        faso: {
          50: "#E8F8EF",
          100: "#C6EED7",
          200: "#93DFB4",
          300: "#56CC8A",
          400: "#22B868",
          500: "#00A651",
          600: "#008C45",
          700: "#007A3D",
          800: "#00612F",
          900: "#004B25",
          950: "#002F17",
        },
        rouge: { DEFAULT: "#E30613" },
        jaune: { DEFAULT: "#FFD000" },
        nuit: { DEFAULT: "#0B1F2D" },
        clair: { DEFAULT: "#F4F6F8" },
      },
      fontFamily: {
        sans: ["Poppins", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
};
