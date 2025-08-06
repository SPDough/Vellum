import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
  build: {
    target: 'node14',
    rollupOptions: {
      external: ['@rollup/rollup-linux-x64-gnu']
    }
  },
  esbuild: {
    target: 'node14'
  }
})