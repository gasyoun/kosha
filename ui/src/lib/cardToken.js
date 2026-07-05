// card_token: filesystem/URL-safe encoding of an SLP1 key.
//
// Exact JS twin of scripts/build_static_cache.py's card_token() and the
// snippet documented in docs/README.md. SLP1 is case-significant (K != k) but
// many checkouts are case-insensitive, so raw keys collide. Keep [a-z0-9]
// verbatim; escape every other UTF-8 byte (uppercase, punctuation, '_'
// itself) as _<hexbyte>. Lossless, ASCII-only. Used both for per-lemma card
// shards (docs/cards/) and the K2b paradigm/reverse shards (docs/inflect/data/).
const enc = new TextEncoder();

export function cardToken(slp1) {
  let out = '';
  for (const b of enc.encode(slp1)) {
    out +=
      (b >= 97 && b <= 122) || (b >= 48 && b <= 57)
        ? String.fromCharCode(b)
        : '_' + b.toString(16).padStart(2, '0');
  }
  return out;
}

// Reverse-index bucket key: the token of the form's first two SLP1 code units.
// Sharding the 3.2M-form reverse index by a 2-char prefix keeps each fetched
// bucket small (the browser never loads the whole index). Kept in sync with
// scripts/build_paradigms.py reverse_bucket().
export function reverseBucket(formSlp1) {
  return cardToken((formSlp1 || '').slice(0, 2));
}
