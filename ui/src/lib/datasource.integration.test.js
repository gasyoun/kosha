// Integration test: the static data path the UI actually uses, exercised
// against the committed demo shards (docs/inflect/data/) — no mocks of the data
// itself, only a fetch() shim that maps URLs to files on disk. This is the
// static half of K2b-2; the API half is covered by tests/test_paradigms.py.
import { describe, it, expect, beforeAll, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const REPO = join(here, '..', '..', '..'); // ui/src/lib -> repo root

// vite.config sets base '/kosha/inflect/', so datasource computes
// SITE_ROOT='/kosha/', DATA='/kosha/inflect/data/'. Map those onto the on-disk
// static tier (docs/inflect/data, docs/cards, docs/js/data).
function urlToPath(url) {
  if (url.startsWith('/kosha/inflect/data/'))
    return join(REPO, 'docs', 'inflect', url.slice('/kosha/inflect/'.length));
  if (url.startsWith('/kosha/cards/'))
    return join(REPO, 'docs', url.slice('/kosha/'.length));
  if (url === '/kosha/js/data/lemmas.json')
    return join(REPO, 'docs', 'js', 'data', 'lemmas.json');
  throw new Error(`unmapped url ${url}`);
}

beforeAll(() => {
  vi.stubGlobal('window', {}); // no KOSHA_API -> static path
  vi.stubGlobal('fetch', async (url) => {
    let path;
    try { path = urlToPath(url); } catch { return { ok: false, status: 404 }; }
    try {
      const text = readFileSync(path, 'utf8');
      return { ok: true, status: 200, json: async () => JSON.parse(text) };
    } catch {
      return { ok: false, status: 404 };
    }
  });
});

// import AFTER the window stub so `const API = window.KOSHA_API ?? null` is null.
let ds;
beforeAll(async () => { ds = await import('./datasource.js'); });

describe('forward paradigm (static)', () => {
  it('renders the rAma m_a grid from the committed shard', async () => {
    const p = await ds.getParadigm('rAma');
    expect(p.lemma_iast).toBe('rāma');
    const m_a = p.models.find((m) => m.model === 'm_a');
    expect(m_a.cells.nom.sg).toEqual(['rAmaH']);
    expect(m_a.cells.instr.sg).toEqual(['rAmeRa']);
  });
});

describe('reverse analyze (static, stages 1-2)', () => {
  it('resolves bhagavān -> bhagavat with provenance', async () => {
    const r = await ds.analyzeForm('BagavAn');
    expect(r.resolved_by).toBe('inflections');
    expect(r.lemmas.map((l) => l.lemma_iast)).toContain('bhagavat');
  });
  it('resolves the ambiguous dharmakṣetre to dharmakṣetra', async () => {
    const r = await ds.analyzeForm('Darmakzetre');
    expect(r.lemmas.map((l) => l.lemma_iast)).toContain('dharmakṣetra');
    expect(r.analyses.length).toBeGreaterThan(1); // genuine case ambiguity
  });
  it('reports honest static miss for a segmentation-only form', async () => {
    const r = await ds.analyzeForm('tattvamasi'); // needs vidyut segmentation
    expect(r.resolved_by).toBeNull();
    expect(r.segmentation_available).toBe(false);
  });
});

describe('entry cross-link (static card)', () => {
  it('loads dictionary entries for a stem', async () => {
    const entries = await ds.getEntry('BU'); // bhū, has a committed card
    expect(entries.length).toBeGreaterThan(0);
    expect(entries[0]).toHaveProperty('rendered_html');
  });
});
