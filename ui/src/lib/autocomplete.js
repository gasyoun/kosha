// Prefix autocomplete over the shared 323k-lemma index (docs/js/data/lemmas.json).
//
// The rows are sorted by SLP1 key, so a prefix query is a binary-search range
// seek — NOT a full 323k scan (the .ai_state "Search-latency" note: the API had
// the same latent LIKE-scan issue and moved to a case-sensitive range seek).
// SLP1 is case-significant, so comparisons are plain code-unit ordinal — no
// case folding (which would over-match K==k).

// Lower bound: first index whose slp1 >= key.
function lowerBound(rows, key) {
  let lo = 0, hi = rows.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (rows[mid][0] < key) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

// Return up to `limit` {slp1, iast, dicts} whose SLP1 starts with prefixSlp1.
export function prefixSuggest(index, prefixSlp1, limit = 20) {
  if (!prefixSlp1) return [];
  const rows = index.rows;
  const out = [];
  let i = lowerBound(rows, prefixSlp1);
  for (; i < rows.length && out.length < limit; i++) {
    const slp1 = rows[i][0];
    if (!slp1.startsWith(prefixSlp1)) break; // past the range: stop (sorted)
    out.push({ slp1, iast: rows[i][1], dicts: rows[i][2] });
  }
  return out;
}
