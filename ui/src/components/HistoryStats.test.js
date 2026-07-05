// H205 Phase C: component-level tests for History.svelte / Stats.svelte.
// Both components are no-ops without a live API (R1/R5/R12 — no static
// fallback exists for personal history or live aggregate stats), so
// coverage here is: (a) hidden entirely when the API is unset, (b) renders
// real data when a stubbed API responds. `../lib/datasource.js`'s `API`
// export is mocked directly via vi.doMock. Each test re-imports the
// component under a unique query-string specifier (`?case=...`) so Vite/
// vitest treats it as a fresh module picking up the current mock, instead
// of reusing a previous test's cached instance — full vi.resetModules()
// would also reload svelte's own runtime and break effect-context tracking
// (`effect_orphan`), so it is deliberately avoided here.
import { describe, it, expect, vi } from 'vitest';
import { render, waitFor } from '@testing-library/svelte';

describe('History.svelte', () => {
  it('hides itself when no live API is configured', async () => {
    vi.doMock('../lib/datasource.js', () => ({ API: null }));
    const History = (await import('./History.svelte?case=no-api')).default;
    const { container } = render(History, { props: { out: 'deva' } });
    expect(container.textContent).toContain('requires the live API');
  });

  it('renders returned history entries against a stubbed API', async () => {
    vi.doMock('../lib/datasource.js', () => ({ API: 'http://test-api' }));
    vi.stubGlobal('fetch', async (url) => {
      if (String(url).includes('/api/v1/history')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            query: { limit: 50, offset: 0, total: 1 },
            results: [{ ts: '2026-07-05T00:00:00Z', query_raw: 'rāma', query_slp1: 'rAma', mode: 'auto', results_total: 3 }],
          }),
        };
      }
      return { ok: false, status: 404 };
    });
    const History = (await import('./History.svelte?case=with-api')).default;
    const { container } = render(History, { props: { out: 'iast' } });
    await waitFor(() => expect(container.textContent).toContain('rāma'));
    expect(container.textContent).toContain('clear history');
    vi.unstubAllGlobals();
  });
});

describe('Stats.svelte', () => {
  it('hides itself when no live API is configured', async () => {
    vi.doMock('../lib/datasource.js', () => ({ API: null }));
    const Stats = (await import('./Stats.svelte?case=no-api')).default;
    const { container } = render(Stats, { props: { out: 'deva' } });
    expect(container.textContent).toContain('require the live API');
  });

  it('renders summary + top terms against a stubbed API', async () => {
    vi.doMock('../lib/datasource.js', () => ({ API: 'http://test-api' }));
    vi.stubGlobal('fetch', async (url) => {
      const u = String(url);
      if (u.includes('/api/v1/stats/summary')) {
        return { ok: true, status: 200, json: async () => ({ total_searches: 24, unique_visitors: 3, top_terms: [] }) };
      }
      if (u.includes('/api/v1/stats/timeseries')) {
        return { ok: true, status: 200, json: async () => ({ interval: 'day', points: [{ day: '2026-07-05', count: 24 }] }) };
      }
      if (u.includes('/api/v1/stats/top')) {
        return { ok: true, status: 200, json: async () => ({ results: [{ query_slp1: 'rAma', count: 1 }] }) };
      }
      return { ok: false, status: 404 };
    });
    const Stats = (await import('./Stats.svelte?case=with-api')).default;
    const { container } = render(Stats, { props: { out: 'iast' } });
    await waitFor(() => expect(container.textContent).toContain('total searches'));
    expect(container.textContent).toContain('24');
    expect(container.textContent).toContain('rāma');
    vi.unstubAllGlobals();
  });
});
