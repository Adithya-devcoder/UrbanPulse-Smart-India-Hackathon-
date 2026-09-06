/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Backgrounds
        bg: {
          primary: '#171717',
          secondary: '#222222',
          card: '#1E1E1E',
          elevated: '#2B2A27',
        },
        // Borders
        border: {
          DEFAULT: '#383530',
          light: '#454240',
        },
        // Primary accent — Rust/Orange (replaces cyan)
        cyan: {
          primary: '#D47A45',
          secondary: '#E08A5A',
          muted: '#3A2419',
        },
        // Secondary/sand (replaces amber-warning role)
        amber: {
          warning: '#C7B89D',
          muted: '#352E26',
        },
        // Critical — Signal Red
        coral: {
          critical: '#D9534F',
          muted: '#3A1E1D',
        },
        // Success — Muted Green
        success: {
          DEFAULT: '#6F9E75',
          muted: '#1E2E20',
        },
        // Text
        text: {
          primary: '#E8E3D8',
          secondary: '#9E9A8E',
          muted: '#6B6760',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': '0.65rem',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
      },
      boxShadow: {
        'card': '0 2px 12px rgba(0,0,0,0.4)',
        'elevated': '0 4px 24px rgba(0,0,0,0.5)',
        'cyan-glow': '0 0 12px rgba(212,122,69,0.18)',
        'cyan-glow-md': '0 0 20px rgba(212,122,69,0.28)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
