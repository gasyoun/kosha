import { describe, it, expect } from 'vitest';
import { detectScheme, toSlp1Auto, fromSlp1Out } from './translit.js';
import { cardToken, reverseBucket } from './cardToken.js';
import { prefixSuggest } from './autocomplete.js';

describe('auto-detect + normalise (K2b-4)', () => {
  it('detects the three input scripts', () => {
    expect(detectScheme('राम')).toBe('deva');
    expect(detectScheme('rāma')).toBe('iast');
    expect(detectScheme('rAma')).toBe('slp1');
  });

  it('normalises rāma / राम / rAma to one SLP1 key', () => {
    for (const s of ['rāma', 'राम', 'rAma']) expect(toSlp1Auto(s, 'auto')).toBe('rAma');
  });

  it('normalises the reverse exit forms', () => {
    expect(toSlp1Auto('bhagavān', 'auto')).toBe('BagavAn');
    expect(toSlp1Auto('rāmeṇa', 'auto')).toBe('rAmeRa');
    expect(toSlp1Auto('dharmakṣetre', 'auto')).toBe('Darmakzetre');
  });
});

describe('Devanagari-default rendering', () => {
  it('composes vowel matras / conjuncts (not naive char-map)', () => {
    expect(fromSlp1Out('rAma', 'deva')).toBe('राम');
    expect(fromSlp1Out('rAmasya', 'deva')).toBe('रामस्य');
    expect(fromSlp1Out('Bagavantam', 'deva')).toBe('भगवन्तम्');
  });
  it('round-trips iast', () => {
    expect(fromSlp1Out('rAma', 'iast')).toBe('rāma');
  });
});

describe('card_token / reverse bucket parity with Python', () => {
  it('matches the documented tokens', () => {
    expect(cardToken('rAma')).toBe('r_41ma');
    expect(cardToken('BU')).toBe('_42_55');
    expect(cardToken('kf')).toBe('kf');
    expect(reverseBucket('BagavAn')).toBe('_42a');
    expect(reverseBucket('rAmeRa')).toBe('r_41');
    expect(reverseBucket('Darmakzetre')).toBe('_44a');
  });
});

describe('autocomplete prefix seek (range, not full scan)', () => {
  const index = {
    fields: ['slp1', 'iast', 'dicts'],
    // sorted by SLP1 code-unit order
    rows: [
      ['ka', 'ka', 'MW'],
      ['kavi', 'kavi', 'MW'],
      ['kf', 'kṛ', 'MW'],
      ['rAga', 'rāga', 'MW'],
      ['rAma', 'rāma', 'MW'],
      ['rAmAyaRa', 'rāmāyaṇa', 'MW'],
    ],
  };
  it('returns only the prefix range', () => {
    const out = prefixSuggest(index, 'rAm', 10);
    expect(out.map((s) => s.slp1)).toEqual(['rAma', 'rAmAyaRa']);
  });
  it('is case-significant (K != k)', () => {
    expect(prefixSuggest(index, 'k', 10).length).toBe(3); // ka, kavi, kf — not rA...
  });
  it('respects the limit', () => {
    expect(prefixSuggest(index, 'k', 2).length).toBe(2);
  });
  it('empty prefix -> no suggestions', () => {
    expect(prefixSuggest(index, '', 10)).toEqual([]);
  });
});
