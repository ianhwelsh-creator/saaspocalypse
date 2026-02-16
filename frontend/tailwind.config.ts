import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          primary: '#faf8f5',
          secondary: '#ffffff',
          tertiary: '#f2ede6',
          raised: '#ece6dc',
          floating: '#ffffff',
        },
        arena: {
          text: '#2d2b29',
          'text-secondary': '#413d39',
          'text-tertiary': '#666058',
          muted: '#8a8480',
          border: '#edebe9',
          'border-medium': '#e0dbd5',
          link: '#2b7fd4',
          positive: '#1a9d3f',
          negative: '#d63939',
          warning: '#d49b1a',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['DM Mono', 'ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config
