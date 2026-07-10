// P5 operator parser + view-mode + word-hash unit tests (H537).
import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  parseQuery, loadViewMode, saveViewMode, DEFAULT_VIEW,
  wordHash, parseWordHash, groupByDict,
} from './query.js';

describe('parseQuery — P5 §4 operators', () => {
  it('bare input auto-routes', () => {
    expect(parseQuery('rAma')).toEqual({ kind: 'auto', value: 'rAma' });
    expect(parseQuery('  bhagavān ')).toEqual({ kind: 'auto', value: 'bhagavān' });
  });
  it('empty is its own kind', () => {
    expect(parseQuery('')).toEqual({ kind: 'empty', value: '' });
    expect(parseQuery('   ')).toEqual({ kind: 'empty', value: '' });
  });
  it('root: operator (case-insensitive, space-tolerant)', () => {
    expect(parseQuery('root:BU')).toEqual({ kind: 'root', value: 'BU' });
    expect(parseQuery('Root: BU')).toEqual({ kind: 'root', value: 'BU' });
    expect(parseQuery('  ROOT :  kf ')).toEqual({ kind: 'root', value: 'kf' });
  });
  it('sandhi: operator forces the reverse pipeline', () => {
    expect(parseQuery('sandhi:tattvamasi')).toEqual({ kind: 'sandhi', value: 'tattvamasi' });
    expect(parseQuery('SANDHI: rāmeṇa')).toEqual({ kind: 'sandhi', value: 'rāmeṇa' });
  });
  it('a colon that is not an operator stays auto', () => {
    expect(parseQuery('foo:bar')).toEqual({ kind: 'auto', value: 'foo:bar' });
  });
});

describe('view mode persistence (P5-2)', () => {
  beforeEach(() => {
    const store = {};
    vi.stubGlobal('localStorage', {
      getItem: (k) => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = String(v); },
    });
  });
  it('defaults to adaptive on first visit', () => {
    expect(loadViewMode()).toBe(DEFAULT_VIEW);
    expect(DEFAULT_VIEW).toBe('adaptive');
  });
  it('round-trips a saved choice', () => {
    saveViewMode('gloss');
    expect(loadViewMode()).toBe('gloss');
  });
  it('ignores an invalid stored value', () => {
    saveViewMode('nonsense');
    expect(loadViewMode()).toBe(DEFAULT_VIEW);
  });
});

describe('word hash routing', () => {
  it('round-trips an slp1 key', () => {
    expect(parseWordHash(wordHash('rAma'))).toBe('rAma');
    expect(parseWordHash(wordHash('a_b'))).toBe('a_b');
  });
  it('non-word hashes return null', () => {
    expect(parseWordHash('#/stats')).toBeNull();
    expect(parseWordHash('')).toBeNull();
  });
});

describe('groupByDict — P5-1 fixed order', () => {
  it('orders MW → PWG → AP90, drops absent dicts', () => {
    const g = groupByDict([
      { dict: 'ap90', L: '1' }, { dict: 'mw', L: '1' }, { dict: 'mw', L: '2' },
    ]);
    expect(g.map((x) => x.dict)).toEqual(['mw', 'ap90']);
    expect(g[0].entries).toHaveLength(2);
  });
});
