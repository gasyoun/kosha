// K2b-2 data-source shim: ONE code path per feature, exercised both ways.
//
//   const API = window.KOSHA_API ?? null;
//
// When window.KOSHA_API is set to a kosha FastAPI base URL, every lookup hits
// the live API (`/api/v1/...`) for freshness. Otherwise it fetches the
// pre-generated static JSON that ships with the Pages deploy — so the tool
// works fully on gasyoun.github.io with no live server (R1/R5/R12-clean), and
// degrades gracefully. The API-when-present path is kosha's OWN server, never a
// live third-party service (RISKS.md R12).
import { cardToken, reverseBucket } from './cardToken.js';

export const API = typeof window !== 'undefined' ? (window.KOSHA_API ?? null) : null;

// BASE_URL is /kosha/inflect/ on Pages, / in dev. The shared autocomplete
// index (docs/js/data/) and per-lemma cards (docs/cards/) live one level up
// from the app, at the site root.
const BASE = import.meta.env.BASE_URL || '/';
const SITE_ROOT = BASE.replace(/inflect\/?$/, '');
const DATA = BASE.replace(/\/?$/, '/') + 'data/';

async function getJson(url) {
  const r = await fetch(url);
  if (!r.ok) {
    const e = new Error(`fetch ${url} -> ${r.status}`);
    e.status = r.status;
    throw e;
  }
  return r.json();
}

// ---- Forward: stem -> paradigm ----------------------------------------------
export async function getParadigm(slp1Lemma) {
  if (API) {
    const j = await getJson(`${API}/api/v1/paradigm/${encodeURIComponent(slp1Lemma)}?in=slp1`);
    return j.results[0];
  }
  return getJson(`${DATA}paradigms/${cardToken(slp1Lemma)}.json`);
}

// ---- Reverse: paste-anything analyze ----------------------------------------
export async function analyzeForm(slp1Form) {
  if (API) {
    const j = await getJson(`${API}/api/v1/forms/${encodeURIComponent(slp1Form)}/analyze?in=slp1`);
    return j.results[0];
  }
  // Static fallback resolves stages 1-2 (exact inflection / forms hits) from a
  // prefix-bucketed reverse index. Stage-3 vidyut segmentation cannot run in a
  // static browser context, so a sandhied/compound miss reports
  // segmentation_available:false — the same honest-degradation contract the API
  // exposes when its vendored vidyut data is absent.
  let bucket;
  try {
    bucket = await getJson(`${DATA}reverse/${reverseBucket(slp1Form)}.json`);
  } catch (e) {
    if (e.status === 404) bucket = {};
    else throw e;
  }
  const hit = bucket[slp1Form];
  if (!hit) {
    return { resolved_by: null, analyses: [], lemmas: [], segmentation_available: false, static: true };
  }
  return {
    resolved_by: hit.resolved_by,
    analyses: hit.analyses || [],
    forms_witnesses: hit.forms_witnesses || [],
    lemmas: hit.lemmas || [],
    static: true,
  };
}

// ---- Autocomplete index (shared with the P2 static tier) --------------------
let _lemmaIndex = null;
export async function loadLemmaIndex() {
  if (_lemmaIndex) return _lemmaIndex;
  if (API) {
    // The API has no bulk index dump; autocomplete always uses the shared
    // static lemmas.json even in API mode (it is the canonical index per
    // H183 §3 — "do not build a second index").
  }
  const j = await getJson(`${SITE_ROOT}js/data/lemmas.json`);
  // Columnar: {fields:["slp1","iast","dicts"], rows:[[slp1,iast,dicts],...]}.
  // Rows are already sorted by slp1 (the generator emits them sorted), which
  // lets autocomplete binary-search the prefix range instead of scanning 323k.
  _lemmaIndex = { fields: j.fields, rows: j.rows };
  return _lemmaIndex;
}

// A lemma's dictionary entries (the K3-folded cross-link target), rendered
// in-app. Both the static card (docs/cards/<token>.json) and the live
// /api/v1/lemma response share the {results:[{dict,L,headword,rendered_html,
// scan_url,...}]} shape, so one unwrap serves both. Returns [] when the lemma
// has no entry (e.g. an attested stem with no dict headword) instead of throwing.
export async function getEntry(slp1Lemma) {
  const url = API
    ? `${API}/api/v1/lemma/${encodeURIComponent(slp1Lemma)}?in=slp1`
    : `${SITE_ROOT}cards/${cardToken(slp1Lemma)}.json`;
  try {
    const j = await getJson(url);
    return j.results || [];
  } catch (e) {
    if (e.status === 404) return [];
    throw e;
  }
}
