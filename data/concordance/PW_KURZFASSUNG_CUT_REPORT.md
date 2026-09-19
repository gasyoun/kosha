# PW × PWG Kurzfassung cut measure — sense-block diff (H4805)

_Built 2026-09-19 · OxAlpha (opencode/z-ai/glm-5.3-flash) · script: scripts/build_pw_kurzfassung_cut.py_

## What was measured

- **PW** (csl-orig v02/pw, Böhtlingk–Roth 7-vol): 158,370 entries, 131,443 `<div>` boundaries, 289,813 sense blocks.
- **PWG** (v02/pwg, Kurzfassung): 123,357 entries, 100,080 `<div>` boundaries, 223,437 sense blocks.
- Headword grid (form_key of k1, `*`/`˚` stripped, case preserved): 151,461 keys.
- `{{Lbody}}` stubs excluded: pw 12,186, pwg 9.

## The cut, in numbers

| metric | value |
|---|---|
| shared headwords | 96,305 |
| headwords living only in PW (whole-entry cut) | 45,382 |
| headwords only in PWG (Kurzfassung additions/splits) | 9,774 |
| PW sense blocks with a PWG partner | 89,579 |
| **PW sense blocks CUT (no PWG partner)** | **200,234** |
| cut share of PW block mass | 69.1% |
| headwords carrying any cut | 105,410 |

## Method (short)

Sense blocks = `<div` boundaries of the Cologne text (head region before the first `<div` is block 0). PW→PWG greedy best-match per headword: shared folded `<ls>` witnesses, score Σ1/df ≤ 1, edge at the frozen house τ=0.30 (H3744); plus German-gloss token Jaccard ≥ 0.50, legal here because PW and PWG share one metalanguage (de) — the sense_align.py English-only fence governs the cross-language table, not this de↔de pair. Each PWG block is claimed at most once (best-match, not reachability). CUT = PW block with no PWG partner; whole-entry cut = headword absent from PWG.

## Queue for pwg_ru (top 15 by cut mass)

| k1 | status | pw blocks | pwg blocks | cut | sample of cut content |
|---|---|---|---|---|---|
| vart | shared | 772 | 385 | 539 | verlaufen  ∕  vor sich gehen, einen Verlaufen nehmen, von Statten gehen; wie geht es der  ∕  sich irgendwo befinden, weilen, |
| sTA | shared | 680 | 496 | 369 | stehen, — auf in oder an; dastehen, vor Einem stehen, stillstehen, stehen bleiben, Halt machen, zum   ∕  bei Etwas bleiben |
| i | shared | 530 | 412 | 358 | gehen, wandern, fahren, fliessen, sich fortbewegen, — verbreiten; kommen; gekommen in  ∕  hingehen zu, sich begeben in, na |
| DA | shared | 468 | 358 | 306 | setzen, legen, stellen, einfügen, einbringen, — in oder auf; den Stock legen auf,; Strafe verhängen   ∕  hinbringen —, hin |
| har | shared | 530 | 351 | 295 | halten, tragen, auf oder in  ∕  herbeischaffen, — bringen, holen  ∕  ab-, wegwenden |
| gam | shared | 367 | 295 | 245 | kommen —, hingehen —, sich begeben nach, in, zu oder auf, gelangen nach oder zu, zu Theil werden;  ∕  gehen,; beiwohnen; m |
| han | shared | 380 | 244 | 245 | abschlagen, herunterschlagen  ∕  tödten; mit dem Tode bestrafen, hinrichten lassen  ∕  verletzen; beissen |
| kar | shared | 365 | 351 | 234 | bearbeiten, zubereiten, bestellen  ∕  machen, machen zu; zur Arzenei gemacht  ∕  Etwas; meist; Was?; mit Etwas; anfangen, ei |
| pad | shared | 365 | 267 | 214 | hinausgehen über; überspringen  ∕  versäumen, übertreten  ∕  verstreichen lassen |
| yuj | shared | 335 | 207 | 195 | schirren, anschirren mit; fahrend mit  ∕  anspannen; in Thätigkeit setzen, in Gebrauch nehmen, zurüsten, ausrüsten; verric |
| var | shared | 230 | 89 | 193 | verhüllen, bedecken, zudecken  ∕  umschliessen, umringen  ∕  schliessen |
| sad | shared | 267 | 140 | 183 | versunken  ∕  niedergesunken, erschlafft; matt, erloschen; mitgenommen, erschöpft  ∕  todt |
| BU | shared | 279 | 188 | 176 | werden, — zu oder Etwas; entstehen, geschehen, eintreten, sich erheben; zum Vorschein kommen, — aus;  ∕  kann —, mag sein, |
| viS | shared | 335 | 238 | 171 | sich niederlassen, hineintreten —, eingehen —, einziehen —, sich hineinbegeben —, hineinschlüpfen —,  ∕  sich; begeben  ∕  z |
| sar | shared | 250 | 147 | 168 | rasch laufen, gleiten, fliessen, zerrinnen; wehen; wettlaufen,; sich anstrengen; aufschnellen  ∕  sich entfernen, entlaufe |

Full queue: `data/concordance/pw_pwg_headword_grid.tsv` (sorted cut-first); per-block diff: `data/concordance/pw_pwg_cut_diff.tsv`.

## Verify — headword-grid recount

The build hard-fails unless an independent recount (raw `^<L>` lines minus `{{Lbody` stubs; raw `<div` occurrences; grid sums vs parsed totals) reproduces the parse exactly, and the printed canaries (`aMSa` ≥ 8 blocks, `aMSaka`, `agni`, `nAgadanta`) hold. Run: `python scripts/build_pw_kurzfassung_cut.py --report` → `VERIFY: PASS`.

## Limitations

- Block pairing is evidence-based, not a philological reading: a PW block whose PWG counterpart was merged or reworded without shared witnesses or shared German wording counts as cut (over-count risk); the diff TSV keeps the gloss of every such block so a human can eyeball the queue tops.
- Footnote (`<F>`) text stays inside its block; witness keys are folded with the house prefix rule (≥4 chars).
- One-to-one claim discipline: a PWG merge of several PW senses leaves the surplus PW blocks in the cut — the conservative direction for a queue.

## Registration

- kosha datasets.json: `pw-pwg-kurzfassung-cut` (tier public, derived from the Cologne csl-orig digital text).
- Uprava interlinks edge: csl-orig/pw → kosha (consumer verified: this build).
