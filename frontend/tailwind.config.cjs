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
          light: '#ffb84d',
          DEFAULT: '#ffa116',
          dark: '#e58e09',
        },
        background: {
          light: '#f4f4f5',
          DEFAULT: '#0a0a0a',
          dark: '#050505',
        },
        surface: {
          light: '#ffffff',
          DEFAULT: '#1a1a1a',
          elevated: '#282828',
          dark: '#222222',
        },
        border: {
          DEFAULT: '#2f2f2f',
          light: '#3e3e3e',
        },
        accent: {
          DEFAULT: '#2cbb5d',
          dark: '#249a4c',
        },
        warning: {
          DEFAULT: '#ffc01e',
          dark: '#d97706',
        },
        danger: {
          DEFAULT: '#ef4743',
          dark: '#dc2626',
        },
        text: {
          DEFAULT: '#eff1f6',
          muted: '#9ca3af',
        },
      },
    },
  },
  plugins: [],
};
