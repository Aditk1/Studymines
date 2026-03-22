/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        poppins: ['Poppins', 'sans-serif'],
        serif: ['Source Serif 4', 'serif'],
      },
      tracking: {
        tighter: '-0.05em',
      }
    },
  },
  plugins: [],
}
