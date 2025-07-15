import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// see https://stackoverflow.com/questions/73834404/react-uncaught-referenceerror-process-is-not-defined
// otherwise use import.meta.env.VITE_BACKEND_API_URL and expose it as such with the VITE_ prefix
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  return {
    define: {
      'process.env': env,
    },
    plugins: [react({ 
      // Enable Fast Refresh for better HMR performance
      fastRefresh: true,
      // Use SWC for faster compilation
      jsxRuntime: 'automatic'
    })],
    optimizeDeps: { 
      esbuildOptions: { target: 'es2020' },
      // Pre-bundle common dependencies
      include: [
        'react',
        'react-dom',
        '@mui/material',
        '@mui/icons-material',
        '@heroicons/react',
        'axios',
        'react-router-dom'
      ]
    },
    server: {
      // Enable file system cache
      fs: {
        cachedChecks: false
      },
      // Increase verbosity for debugging
      hmr: {
        overlay: true
      }
    },
    logLevel: 'info',
    build: {
      // Use esbuild for faster builds
      target: 'es2020',
      // Enable source maps only in development
      sourcemap: mode === 'development',
      // Increase chunk size warning limit
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          // Manual chunk splitting for better caching
          manualChunks: {
            vendor: ['react', 'react-dom'],
            mui: ['@mui/material', '@mui/icons-material'],
            router: ['react-router', 'react-router-dom']
          }
        }
      }
    }
  };
});
