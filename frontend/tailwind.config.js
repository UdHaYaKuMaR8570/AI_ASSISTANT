/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: {
          50: '#FDFCF9',
          100: '#FAF6F0',
          200: '#F2ECE1',
          300: '#EADFD3',
          400: '#D5C4B1',
        },
        ink: {
          DEFAULT: '#1A1611',
          light: '#423A31',
          muted: '#73685C',
          faint: '#A69B8F',
        },
        coral: {
          50: '#FDF3EE',
          100: '#FCE6DC',
          500: '#E05D38',
          600: '#C94C28',
          700: '#A7381A',
        },
        sage: {
          50: '#F3F6F3',
          500: '#4F775B',
          600: '#3D5E46',
        },
      },
      fontFamily: {
        serif: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      maxWidth: {
        prose: '68ch',
      },
    },
  },
  plugins: [],
}
