import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { svelteTesting } from '@testing-library/svelte/vite';

// The app ships into ../docs/inflect/ so MG's existing GitHub Pages deploy
// (which serves the committed docs/ tree) picks it up with no new deploy path.
// On Pages the app lives at https://gasyoun.github.io/kosha/inflect/, so the
// base is /kosha/inflect/. Data (paradigm/reverse shards, lemmas.json) is
// fetched relative to import.meta.env.BASE_URL — see src/lib/datasource.js.
export default defineConfig({
  plugins: [svelte(), svelteTesting()],
  base: '/kosha/inflect/',
  build: {
    outDir: '../docs/inflect',
    emptyOutDir: false, // never wipe committed data/ shards under docs/inflect/
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
