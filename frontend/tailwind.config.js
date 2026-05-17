/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Nunito', 'system-ui', 'sans-serif'],
      },
      colors: {
        kb: {
          pink: '#FFB7C5',
          lavender: '#C8B8F8',
          mint: '#A8EED4',
          peach: '#FFD4B8',
          coral: '#FF8FA3',
          cream: '#FFF8F0',
          white: '#FFFFFF',
          muted: '#EDE8F5',
          black: '#000000',
        },
      },
      boxShadow: {
        'brutal-sm': '3px 3px 0px #000000',
        'brutal-md': '5px 5px 0px #000000',
        'brutal-lg': '8px 8px 0px #000000',
        'brutal-none': '0px 0px 0px #000000',
        'brutal-pink': '5px 5px 0px #FFB7C5',
      },
      borderWidth: {
        '3': '3px',
      },
      animation: {
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}

// Made with Bob
