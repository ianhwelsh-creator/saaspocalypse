import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          primary: '#ffffff',
          secondary: '#ffffff',
          tertiary: '#f8f9fa',
          raised: '#f1f3f5',
          floating: '#ffffff',
        },
        arena: {
          text: '#1a1a2e',
          'text-secondary': '#3d3d5c',
          'text-tertiary': '#6b7280',
          muted: '#9ca3af',
          border: '#f0f0f0',
          'border-medium': '#e5e7eb',
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
