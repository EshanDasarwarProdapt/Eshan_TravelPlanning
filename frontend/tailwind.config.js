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
          50: '#FCFCF9',
          100: '#F7F6F2',
          200: '#EFECE6',
          300: '#E2DFD7',
          400: '#C7C3B8',
          900: '#1C1B18',
        },
        ink: {
          900: '#141413',
          800: '#222220',
          700: '#383734',
          500: '#6E6C65',
          400: '#9C998F',
          200: '#D6D4CC',
        },
        accent: {
          DEFAULT: '#C25E38',
          hover: '#A94E2C',
          light: '#F8EFEA',
          border: '#E8C5B4',
        },
        emerald: {
          subtle: '#EDF6F1',
          border: '#B8DEC7',
          ink: '#1E6B47',
        }
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        display: ['"DM Serif Display"', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        subtle: '0 1px 3px rgba(20, 20, 19, 0.04), 0 1px 2px rgba(20, 20, 19, 0.02)',
        card: '0 4px 20px -2px rgba(20, 20, 19, 0.06)',
      }
    },
  },
  plugins: [],
}
