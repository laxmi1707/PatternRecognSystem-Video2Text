import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // BACKEND_URL (e.g. the AWS CloudFront URL) sends /api, /health and /sop-detector
  // through this dev server to that deployment, so the browser makes no cross-origin
  // calls:  BACKEND_URL=https://xxxx.cloudfront.net npm run dev -- --mode aws
  // (--mode aws skips .env.development, whose absolute API URL bypasses the proxy).
  const remote = loadEnv(mode, process.cwd(), '').BACKEND_URL;
  const to = (local: string) => ({ target: remote || local, changeOrigin: true });
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': to('http://localhost:8000'),
        // the SOP detector service (Evaluation/sop_detector_service.py)
        '/sop-detector': to('http://localhost:8100'),
        '/health': to('http://localhost:8000'),
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: './src/test/setup.ts',
    },
  };
});
