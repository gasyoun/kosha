// kosha K2b — encoding auto-detect + output formatting for the browser.
//
// JS twin of app/transliterate.py. All conversion is delegated to the vendored
// sanskrit-util package (SHARED_CODE.md family #1 — IAST<->SLP1<->Devanagari,
// single org source); this module adds only the "auto" input-scheme sniffer
// and the SLP1->HK output map, exactly like the Python module. The detect
// rules MUST stay identical to detect_scheme() in app/transliterate.py so the
// static tier and the live API normalise a pasted string the same way.
//
// The vendored copy is ui/src/lib/sanskrit-util.mjs — re-copy from
// sanskrit-util/js/index.mjs on package updates; never edit it in place.
import {
  to_slp1,
  from_slp1,
  deva_to_slp1,
  slp1_to_devanagari,
} from './sanskrit-util.mjs';

const DEVA_RE = /[ऀ-ॿ]/;
const IAST_DIACRITICS_RE = /[āīūṛṝḷḹṃṁḥṅñṭḍṇśṣḻ]/;

export function detectScheme(text) {
  if (DEVA_RE.test(text)) return 'deva';
  if (IAST_DIACRITICS_RE.test((text || '').toLowerCase())) return 'iast';
  return 'slp1';
}

export function toSlp1Auto(text, scheme = 'auto') {
  if (scheme === 'auto') scheme = detectScheme(text);
  if (scheme === 'slp1') return text;
  if (scheme === 'deva') return deva_to_slp1(text);
  if (scheme === 'iast' || scheme === 'hk') return to_slp1(text);
  throw new Error(`unknown scheme: ${scheme}`);
}

export function fromSlp1Out(slp1, out = 'iast') {
  if (!slp1) return '';
  if (out === 'slp1') return slp1;
  if (out === 'iast') return from_slp1(slp1);
  // Direct SLP1->Devanagari: composes vowel matras / conjuncts correctly.
  // (iast_to_devanagari in sanskrit-util is a naive char-map that renders each
  // vowel as an independent akṣara — never use it for running Sanskrit.)
  if (out === 'deva') return slp1_to_devanagari(slp1);
  throw new Error(`unknown output scheme: ${out}`);
}

// Convenience: all three renderings of a canonical SLP1 key.
export function allScripts(slp1) {
  return {
    slp1,
    iast: fromSlp1Out(slp1, 'iast'),
    deva: fromSlp1Out(slp1, 'deva'),
  };
}
