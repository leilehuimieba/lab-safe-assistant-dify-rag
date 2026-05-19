/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'system-ui',
          '-apple-system',
          '"Segoe UI"',
          '"PingFang SC"',
          '"Microsoft YaHei"',
          'sans-serif',
        ],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      colors: {
        brand: {
          50: '#ECFDF7',
          100: '#D1FAE5',
          200: '#A7F3D0',
          500: '#0EA5A0',
          600: '#0F766E',
          700: '#115E59',
          ink: '#064E4A',
        },
        dec: {
          answer: '#16A34A',
          guarded: '#2563EB',
          lowconf: '#F59E0B',
          blocked: '#B91C1C',
          emerg: '#DC2626',
          need: '#CA8A04',
          fallback: '#64748B',
        },
        risk: {
          high: '#DC2626',
          mid: '#F59E0B',
          low: '#16A34A',
        },
      },
      borderRadius: {
        card: '16px',
        btn: '12px',
        input: '12px',
        pill: '999px',
      },
      boxShadow: {
        card: '0 14px 30px rgba(15, 23, 42, .08)',
        cardHover: '0 20px 40px rgba(15, 23, 42, .12)',
        pop: '0 24px 60px rgba(15, 23, 42, .18)',
      },
      keyframes: {
        msgIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        bounce: {
          '0%, 80%, 100%': { transform: 'translateY(0)', opacity: '.5' },
          '40%': { transform: 'translateY(-5px)', opacity: '1' },
        },
        flash: {
          '0%': { backgroundColor: '#D1FAE5', borderColor: '#0EA5A0' },
          '100%': { backgroundColor: '#ECFDF7', borderColor: '#A7F3D0' },
        },
      },
      animation: {
        msgIn: 'msgIn .3s ease-out',
        bounce: 'bounce 1.2s ease-in-out infinite',
        flash: 'flash 150ms ease-out',
      },
    },
  },
  plugins: [],
};
