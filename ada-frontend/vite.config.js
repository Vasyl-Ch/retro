import { resolve } from 'path';

export default {
  // Django serves the bundle from STATIC_URL/ada/ — dynamic-import chunks and
  // asset urls must be generated against that prefix, not the site root.
  base: '/static/ada/',
  build: {
    outDir: '../distributor/static/ada',
    assetsDir: 'assets',
    manifest: true,
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'main.js'),
    },
  },
};
