_Created: 18-10-2026 · Last updated: 18-10-2026_

# Sanskritabhyas as an external check on our present-system verb forms

_Created: 18-10-2026_

## Verdict in one paragraph

[sanskritabhyas.in](https://sanskritabhyas.in/en/Verb/List) publishes, per root, a
ten-lakāra conjugation grid in Devanāgarī. It is an **independent witness** — MG confirmed
18-10-2026 that it is *not* derived from Cologne/csl-inflect/MWinflect — so a disagreement
is real evidence, not a shared upstream's echo. Our generator
([MWinflect `calc_tables.txt`](https://github.com/sanskrit-lexicon/MWinflect/blob/main/verbs/pysanskritv2/tables/calc_tables.txt),
ingested here as `inflections` rows `v_<gaṇa>`/`v_p`) covers only the **present system**
(laṭ / laṅ / loṭ / vidhiliṅ) and only **gaṇas 1, 4, 6, 10**. That gives two distinct jobs,
which this lane never mixes:

| Job | Population | Output |
|---|---|---|
| **Verification** | roots in gaṇas 1/4/6/10 | cell-by-cell AGREE / DIFF on the four shared lakāras |
| **Coverage** | the other six lakāras and six gaṇas | a census of what the site has and we do not — never counted as a defect |

The machinery is landed and self-tested; the crawl itself has **not** run yet (status §8).

## 1. What the site publishes

The 2025 archive showed a four-lakāra, `/en/Verb/View/<slug>/…` layout. The live site
(checked 18-10-2026) has moved to a single canonical page per root:

```
https://sanskritabhyas.in/<slug>-Conjugation
```

where `<slug>` is the root list's own slug, `root-gaṇa-dhātupāṭha text`, e.g.
`वॄ-क्र्यादिः-वॄ-वरणे-भरण-इत्येके`. The root list lives at `/en/Verb/List`
(paginated `/en/Verb/List/<n>`, 200 per page in the 2025 capture).

Page anatomy (verified on a saved copy of the वॄ page, 121 KB):

- ten `<h4>` sections in teaching order: Present, Perfect Past, Periphrastic Future, Future,
  Imperative, Imperfect Past, Potential, Benedictive, Aorist, Conditional;
- each followed by `div.declension` holding four `.row`s of four `.col-3` cells —
  header `Singular / Dual / Plural`, then **Third / Second / First Person**;
- each cell is a `span.answer`; alternatives are separated by ` / `
  (`वृणीतात् / वृणीताद् / वृणातु`);
- every section exists **twice** — a `d-none d-lg-block` desktop copy and a `d-lg-none`
  mobile copy with identical values. The grabber skips the mobile copy; a parser that does
  not will double every cell;
- `document.title` carries the pada — `… Active Voice Parasmai Pada …`. Whether an
  ubhayapada root exposes a second (ātmane) page is **not yet known** (open question §8).

Form order in our tables is identical to the site's reading order:
3sg · 3du · 3pl · 2sg · 2du · 2pl · 1sg · 1du · 1pl.

## 2. What we generate

From `calc_tables.txt` (measured 18-10-2026):

| Metric | Value |
|---|---|
| rows | 7,460 |
| distinct roots | 683 |
| lakāras | `pre`, `ipf`, `ipv`, `opt` — the present system only |
| kartari rows (active/middle) | 4,700 |
| kartari cells | 42,300 |
| kartari roots | 608 |
| gaṇa coverage | 1, 4, 6, 10 only (2,812 / 644 / 556 / 688 rows) |

The passive rows (`pada=p`, 2,760) have no counterpart on the site and are out of scope.

## 3. Join contract

| Site | Ours | Note |
|---|---|---|
| `slug.split('-')[0]` | `root` (SLP1) | `to_slp1_auto()`; `भू→BU`, `एध्→eD`, `स्पर्ध्→sparD` |
| slug segment 1 (`भ्वादिः` … `चुरादिः`) | gaṇa `1`…`10` | map in the comparator |
| `Present Tense` | `pre` (laṭ) | |
| `Imperfect Past Tense` | `ipf` (laṅ) | |
| `Imperative Mood` | `ipv` (loṭ) | |
| `Potential Mood` | `opt` (vidhiliṅ) | |
| title `Parasmai` / `Atmane` | `pada` `a` / `m` | |
| rows Third/Second/First | 3sg…1pl flattening | |
| `वृणीतात् / वृणीताद्` | one SLP1 form | a cell AGREES if our form ∈ the variant set |

The other six lakāras have no column in `calc_tables.txt`; they are census rows, not diffs.

## 4. Access: Cloudflare, and why the grabber is a console snippet

Direct fetches are refused — `curl`, the DSH `web_fetch`, headless and headed Playwright,
and the `translate.goog` proxy all return the 403 `Just a moment` interstitial. A plain
Chrome with a debug port reached the page but the process does not survive the harness and
the challenge returns. The working route is therefore **the user's own browser session**:
paste a grabber in DevTools, let the page do the fetches same-origin (cookies included),
download JSONL, parse here.

The grabber (canonical copy: this block) walks the paginated root list, fetches each
`-Conjugation` page at 1.2 s, keeps progress in `localStorage["sa_done"]`, downloads a part
file every 100 roots, and aborts loudly if a challenge page ever appears:

```js
(async () => {
  const DELAY = 1200, CHUNK = 100, LIMIT = 0;           // LIMIT=3 for a smoke test
  const B = 'https://sanskritabhyas.in';
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const get = async u => { const r = await fetch(u, {credentials:'include'}); if (r.status !== 200) throw r.status; return r.text(); };
  const parse = h => new DOMParser().parseFromString(h, 'text/html');
  const dec = s => decodeURIComponent(s);

  const baseList = B + '/en/Verb/List';
  const d0 = parse(await get(baseList));
  const pageUrls = [...new Set([...d0.querySelectorAll('a[href*="/Verb/List/"]')]
    .map(a => new URL(a.getAttribute('href'), baseList).href))];
  const entries = [], seen = new Set();
  for (const [i, pu] of [baseList, ...pageUrls].entries()) {
    const d = i === 0 ? d0 : parse(await get(pu));
    for (const a of d.querySelectorAll('a[href*="Conjugation"],a[href*="/Verb/View/"]')) {
      const href = dec(new URL(a.getAttribute('href'), pu).href);
      let slug, url;
      if (/-Conjugation$/.test(href)) { slug = href.split('/').pop().replace(/-Conjugation$/, ''); url = href; }
      else { slug = href.split('/Verb/View/')[1].replace(/\/+$/, ''); url = `${B}/${encodeURIComponent(slug)}-Conjugation`; }
      if (slug && !seen.has(slug)) { seen.add(slug); entries.push({ slug, url }); }
    }
    await sleep(400);
  }
  console.log(`list pages: ${1 + pageUrls.length} · roots: ${entries.length}`);

  const done = new Set(JSON.parse(localStorage.getItem('sa_done') || '[]'));
  const batch = LIMIT ? entries.filter(e => !done.has(e.slug)).slice(0, LIMIT)
                      : entries.filter(e => !done.has(e.slug));
  let buf = [], part = 0, ok = 0, fail = 0, first = true;
  const flush = () => {
    if (!buf.length) return;
    const blob = new Blob([buf.map(r => JSON.stringify(r)).join('\n')], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `sa_conj_part${String(++part).padStart(3, '0')}.jsonl`;
    a.click(); buf = [];
  };
  for (const { slug, url } of batch) {
    let html;
    try { html = await get(url); }
    catch (e) { fail++; await sleep(DELAY); continue; }
    if (/Just a moment|security verification/i.test(html) && html.length < 20000) { flush(); return; }
    const d = parse(html);
    const title = d.title.replace(/\s+/g, ' ').trim();
    const pada = /Atmane/i.test(title) ? 'atmane' : /Parasmai/i.test(title) ? 'parasmai' : '?';
    const sections = [];
    for (const h of d.querySelectorAll('h4')) {
      const box = h.parentElement && h.parentElement.nextElementSibling;
      if (!box || !box.classList.contains('declension') || box.className.includes('d-lg-none')) continue;
      const rows = [...box.querySelectorAll(':scope > .row')]
        .map(r => [...r.querySelectorAll(':scope > div')].map(c => c.textContent.replace(/\s+/g, ' ').trim()))
        .filter(c => c.length === 4);
      if (rows.length !== 4) continue;
      sections.push({ name: h.textContent.trim(), persons: rows.slice(1).map(r => ({ person: r[0], forms: r.slice(1) })) });
    }
    buf.push({ slug, url, title, pada, sections }); ok++; done.add(slug);
    localStorage.setItem('sa_done', JSON.stringify([...done]));
    if (first && sections.length) { console.log('sanity:', sections[0].persons[0].forms.join(' · ')); first = false; }
    if (buf.length >= CHUNK) flush();
    await sleep(DELAY);
  }
  flush(); console.log(`DONE ok ${ok} fail ${fail}`);
})();
```

## 5. The comparator

[`scripts/sanskritabhyas_compare.py`](https://github.com/gasyoun/kosha/blob/main/scripts/sanskritabhyas_compare.py)
reads the part files, converts Devanāgarī with `kosha.transliterate.to_slp1_auto`, and
prints the two jobs separately:

```sh
python scripts/sanskritabhyas_compare.py ~/Downloads/sa_conj_part*.jsonl \
  --mw ../MWinflect/verbs/pysanskritv2/tables/calc_tables.txt \
  --json-out data/e1/sa_agreement.json
```

**Self-test (18-10-2026, synthetic record built from our own BU row with one cell
deliberately corrupted):**

```
records read: 1 · roots by gaṇa: {'1': 1}
comparable roots: 1 · comparable cells: 9
AGREE 8 (88.9 %) · DIFF 1 · site_empty 0
DIFF {'root': 'BU', 'gana': '1', 'pada': 'a', 'tense': 'pre', 'cell': 4,
      'ours': 'BavaTaH', 'site': 'बवति'}
```

The planted error is caught at the right cell; variant cells (`X / Y`) and the four-lakāra
filter are exercised by the same record.

## 6. Rights

[robots.txt](https://sanskritabhyas.in/robots.txt) is Cloudflare-managed:
`User-agent: *` → `Allow: /`, `Content-Signal: search=yes, ai-train=no, use=reference`.
Reference verification is within the signal; the text must never enter a training corpus.
Raw pages stay local and gitignored (the `data/raw_akshara_*` pattern in `.gitignore`);
only derived measurements and the agreement report are committed. Fetching is one page at
a time at 1.2 s, identified by the user's own browser — the same posture the wisdomlib
skill enforces for a second estate.

## 7. Why not the wisdomlib scraper itself

The wisdomlib programme's code and store live at `E:\Tools\wisdomlib-scrape` on the
live MSI with no remote (re-located 27-10-2026; the former `D:\` path is gone and
chapter-body acquisition remains Cloudflare-blocked). This supersedes the dead-MSI
note in [H6073](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6073-OxAlpha_SanskritCorpora_wisdomlib-next-batch_04.10.26.md).
What transfers is its **discipline** — manifest + checkpoint resume, polite throttle
with one retry class, raw
quarantine → parse → derived-only commits, licence-gated posture. Its executable local
sibling is [`scripts/akshara_pilot_crawl.py`](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_pilot_crawl.py)
(`guarded_fetch` allow-list, 2 s + jitter, `done_keys()` resume); if the site ever becomes
fetchable server-side, the grabber collapses into a copy of that 140-line skeleton with
`ALLOWED_URL` swapped for the two `-Conjugation` patterns.

## 8. Status and open questions

**Status 18-10-2026:** tooling landed and tested; **crawl not run**. Blocked on one
browser-side action (paste the grabber); no server-side fetch path exists.

| # | Open question | How it resolves |
|---|---|---|
| 1 | Does an ubhayapada or ātmanepada root get a second page, or only the titled pada? | the sanity line + `pada` field of the first 5 grabber records |
| 2 | How many roots does the live list hold? | `roots: N` printed by the grabber |
| 3 | Are the site's forms accent-free everywhere, or Vedic roots carry svara? | diff sample inspection |
| 4 | Does the site's data come from a printed dhātupāṭha with optional variants we do not generate? | DIFF triage; if the variants are systematic they become a data question, not a bug |

## 9. Next steps

1. Run the grabber once (smoke: `LIMIT = 3`), confirm the sanity line for भू reads
   `भवति · भवतः · भवन्ति`.
2. Run the full pass; collect `sa_conj_part*.jsonl`.
3. `scripts/sanskritabhyas_compare.py` → agreement by lakāra × pada × gaṇa.
4. File genuine defects upstream on MWinflect (verbs pipeline), never patch here silently.
5. Publish the coverage census (six gaṇas, six lakāras) as the second half of the report.

_Dr. Mārcis Gasūns_
