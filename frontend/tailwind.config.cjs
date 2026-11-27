/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#818cf8',
          DEFAULT: '#6366f1',
          dark: '#4f46e5',
        },
        background: {
          light: '#f4f4f5',
          DEFAULT: '#0b0f17',
          dark: '#06090f',
        },
        surface: {
          light: '#ffffff',
          DEFAULT: '#131924',
          elevated: '#1a2232',
          dark: '#0f141d',
        },
        border: {
          DEFAULT: '#242e42',
          light: '#334155',
        },
        accent: {
          DEFAULT: '#10b981',
          dark: '#059669',
        },
        warning: {
          DEFAULT: '#f59e0b',
          dark: '#d97706',
        },
        danger: {
          DEFAULT: '#f43f5e',
          dark: '#e11d48',
        },
        text: {
          DEFAULT: '#e5e7eb',
          muted: '#94a3b8',
        },
      },
    },
  },
  plugins: [],
};
