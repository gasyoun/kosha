// P5 §6 CSV / Anki export unit tests (H537).
import { describe, it, expect } from 'vitest';
import { toCsv, toAnki, glossOf } from './export.js';

const ROWS = [
  { slp1: 'rAma', iast: 'rāma', deva: 'राम', gloss: 'pleasing, charming', dicts: 'MW PWG' },
  { slp1: 'agni', iast: 'agni', deva: 'अग्नि', gloss: 'fire, god of fire', dicts: 'MW' },
];

describe('toCsv', () => {
  it('emits a header + one row per lookup', () => {
    const csv = toCsv(ROWS);
    const lines = csv.split('\r\n');
    expect(lines[0]).toBe('slp1,iast,devanagari,gloss,dicts');
    expect(lines).toHaveLength(3);
    expect(lines[1]).toContain('rAma');
    expect(lines[1]).toContain('राम');
  });
  it('quotes cells containing commas', () => {
    const csv = toCsv([{ slp1: 'x', iast: 'x', deva: 'क', gloss: 'a, b, c', dicts: 'MW' }]);
    expect(csv).toContain('"a, b, c"');
  });
  it('escapes embedded quotes by doubling', () => {
    const csv = toCsv([{ slp1: 'x', iast: 'x', deva: 'क', gloss: 'the "great" one', dicts: 'MW' }]);
    expect(csv).toContain('"the ""great"" one"');
  });
  it('handles an empty list', () => {
    expect(toCsv([])).toBe('slp1,iast,devanagari,gloss,dicts');
  });
});

describe('toAnki', () => {
  it('is tab-separated front\\tback per note', () => {
    const anki = toAnki(ROWS);
    const lines = anki.split('\n');
    expect(lines).toHaveLength(2);
    const [front, back] = lines[0].split('\t');
    expect(front).toBe('राम · rāma');
    expect(back).toBe('pleasing, charming');
  });
  it('collapses tabs/newlines inside a field so a note stays one line', () => {
    const anki = toAnki([{ deva: 'क', iast: 'ka', gloss: 'line1\nline2\tcol' }]);
    expect(anki.split('\n')).toHaveLength(1);
    expect(anki).toBe('क · ka\tline1 line2 col');
  });
});

describe('glossOf', () => {
  it('strips HTML tags and collapses whitespace', () => {
    expect(glossOf('<span class="ls">MBh.</span>  pleasing,\n charming'))
      .toBe('MBh. pleasing, charming');
  });
  it('truncates with an ellipsis past the limit', () => {
    const g = glossOf('a'.repeat(200), 20);
    expect(g.length).toBe(20);
    expect(g.endsWith('…')).toBe(true);
  });
});
