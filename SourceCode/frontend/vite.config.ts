import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    // Force the mock analysis pipeline in tests regardless of a developer's
    // local .env - the suite is written against simulateAnalysis's behavior.
    env: { VITE_API_BASE_URL: '' },
  },
});
