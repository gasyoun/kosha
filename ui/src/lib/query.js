// P5 §4 — search-box operator parsing + view-mode persistence (H537).
//
// Pure, side-effect-free parsing so it is unit-testable without a DOM. The
// search box hands the raw string to parseQuery(); the app routes on `.kind`.

// Operators (P5 §4): `root:BU` → all lemmas under a root; `sandhi:tattvamasi`
// → force the paste-anything reverse pipeline; bare input auto-routes (a known
// headword → word page; an inflected/sandhied form → reverse analyze). The
// operator prefix is case-insensitive and tolerant of surrounding space.
const OP_RE = /^\s*(root|sandhi)\s*:\s*(.*)$/i;

export function parseQuery(text) {
  const raw = (text || '').trim();
  if (!raw) return { kind: 'empty', value: '' };
  const m = raw.match(OP_RE);
  if (m) {
    const op = m[1].toLowerCase();
    return { kind: op, value: m[2].trim() };
  }
  return { kind: 'auto', value: raw };
}

// View-mode persistence (P5-2): Gloss · Full · Adaptive, Adaptive the first-visit
// default, the choice remembered per-visitor. Shares the SAME localStorage key
// (`kosha_view_mode`) as the static prerender's inline JS (app/word_page.py), so
// a reader's choice carries between the prerendered pages and the SPA.
export const VIEW_KEY = 'kosha_view_mode';
export const VIEW_MODES = ['gloss', 'full', 'adaptive'];
export const DEFAULT_VIEW = 'adaptive';

export function loadViewMode() {
  try {
    const v = localStorage.getItem(VIEW_KEY);
    return VIEW_MODES.includes(v) ? v : DEFAULT_VIEW;
  } catch {
    return DEFAULT_VIEW;
  }
}

export function saveViewMode(v) {
  if (!VIEW_MODES.includes(v)) return;
  try { localStorage.setItem(VIEW_KEY, v); } catch { /* private mode: keep in-memory only */ }
}

// Hash route for the SPA word page: #/w/<slp1>. Hash-based so it works on the
// GitHub Pages static host with no server rewrite (the prerendered /w/<token>.html
// is the crawlable twin; the SPA hash route is the in-app navigation).
export function wordHash(slp1) {
  return `#/w/${encodeURIComponent(slp1)}`;
}

export function parseWordHash(hash) {
  const m = /^#\/w\/(.+)$/.exec(hash || '');
  return m ? decodeURIComponent(m[1]) : null;
}

// Dictionary presentation order + labels (P5-1), shared by the SPA word page.
export const DICT_ORDER = ['mw', 'pwg', 'ap90'];
export const DICT_LABEL = { mw: 'MW', pwg: 'PWG', ap90: 'AP90' };

export function groupByDict(entries) {
  const by = {};
  for (const e of entries || []) (by[e.dict] ||= []).push(e);
  return DICT_ORDER.filter((d) => by[d]).map((d) => ({ dict: d, entries: by[d] }));
}
