import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        // Proxy /api and /health to the FastAPI backend during dev
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8088',
                changeOrigin: true,
            },
            '/health': {
                target: 'http://127.0.0.1:8088',
                changeOrigin: true,
            },
            '/v1': {
                target: 'http://127.0.0.1:8088',
                changeOrigin: true,
            },
        },
    },
    build: {
        outDir: 'dist',
        sourcemap: false,
        chunkSizeWarningLimit: 800,
    },
});
