// Component e2e: mount the real App and drive the H183 exit flows against the
// committed demo shards (static path, no KOSHA_API). Verifies the Svelte wiring
// end-to-end — SearchBox -> getParadigm -> ParadigmTable renders Devanagari by
// default; ReverseAnalyze -> analyzeForm shows provenance + lemma cross-links.
import { describe, it, expect, beforeAll, vi } from 'vitest';
import { render, fireEvent, waitFor } from '@testing-library/svelte';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const REPO = join(here, '..', '..');

// tiny stand-in for the 13 MB lemmas.json so autocomplete stays fast in-test
const LEMMA_INDEX = JSON.stringify({
  fields: ['slp1', 'iast', 'dicts'],
  rows: [['rAga', 'rāga', 'MW'], ['rAma', 'rāma', 'MW'], ['rAmAyaRa', 'rāmāyaṇa', 'MW']],
});

function urlToPath(url) {
  if (url.startsWith('/kosha/inflect/data/'))
    return join(REPO, 'docs', 'inflect', url.slice('/kosha/inflect/'.length));
  if (url.startsWith('/kosha/cards/')) return join(REPO, 'docs', url.slice('/kosha/'.length));
  return null;
}

beforeAll(() => {
  vi.stubGlobal('fetch', async (url) => {
    if (url === '/kosha/js/data/lemmas.json')
      return { ok: true, status: 200, json: async () => JSON.parse(LEMMA_INDEX) };
    const path = urlToPath(url);
    try {
      return { ok: true, status: 200, json: async () => JSON.parse(readFileSync(path, 'utf8')) };
    } catch {
      return { ok: false, status: 404 };
    }
  });
});

describe('forward flow (exit check 1)', () => {
  it('rAma renders the m_a paradigm in Devanagari', async () => {
    const App = (await import('./App.svelte')).default;
    const { container, getByText, getByLabelText } = render(App);
    // P5 made the word page the default tab; the forward flow lives behind its tab.
    await fireEvent.click(getByText(/Stem → paradigm/i));
    const input = getByLabelText(/Sanskrit input/i);
    await fireEvent.input(input, { target: { value: 'rAma' } });
    await fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      // राम (Devanagari) heading appears; रामेण = instr sg cell
      expect(container.textContent).toContain('रामेण');
    }, { timeout: 3000 });
    expect(container.textContent).toContain('राम');
  });
});

describe('word-page flow (P5 exit check)', () => {
  it('rAma opens a word page with MW/PWG/AP90 tabs and the entry', async () => {
    const App = (await import('./App.svelte')).default;
    const { container, getByLabelText } = render(App); // 'word' is the default tab
    const input = getByLabelText(/Sanskrit input/i);
    await fireEvent.input(input, { target: { value: 'rAma' } });
    await fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(container.querySelector('.dict-tabs')).toBeTruthy();
      // every dict panel present in the DOM (crawlable tabs, P5-1)
      expect(container.querySelectorAll('.dict-panel').length).toBeGreaterThanOrEqual(2);
      expect(container.textContent).toContain('band 1');   // rāma is core (band 1)
    }, { timeout: 3000 });
    // the view-mode toggle exists (P5-2)
    expect(container.textContent).toMatch(/Gloss/);
    expect(container.textContent).toMatch(/Adaptive/);
  });

  it('the sandhi: operator routes to the reverse analyser', async () => {
    const App = (await import('./App.svelte')).default;
    const { container, getByLabelText } = render(App);
    const input = getByLabelText(/Sanskrit input/i);
    await fireEvent.input(input, { target: { value: 'sandhi:bhagavān' } });
    await fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(container.textContent).toMatch(/resolved by/i);
      expect(container.textContent).toContain('inflections');
    }, { timeout: 3000 });
  });
});

describe('reverse flow (exit check 2)', () => {
  it('bhagavān resolves with inflections provenance', async () => {
    const App = (await import('./App.svelte')).default;
    const { container, getByText, getByLabelText } = render(App);
    await fireEvent.click(getByText(/Analyse a form/i));
    const box = getByLabelText(/Paste any Sanskrit form/i);
    await fireEvent.input(box, { target: { value: 'bhagavān' } });
    await fireEvent.keyDown(box, { key: 'Enter' });

    await waitFor(() => {
      expect(container.textContent).toMatch(/resolved by/i);
      expect(container.textContent).toContain('inflections');
    }, { timeout: 3000 });
  });
});
