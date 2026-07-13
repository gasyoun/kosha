#!/usr/bin/env python
"""Build the B3 Bloomfield-style parallel-passage concordance (H836 /
CONCORDANCE_ROADMAP Q2).

Normalizes the 245-file `PARA/Polnorazmernye/` export (the "full-size"
meter-to-meter parallel search, canonical per the folder's own README —
`Polnorazmernye-2022-archive/` is the superseded 2022 pass,
`Stopovye/` is a *different method* — per-foot/pada search on a partial
113-of-245-text run, not the same unit of comparison) into one verse-keyed
concordance, per the shared schema in concordance_core.py (RECORD_FIELDS).

Schema of a PARA/Polnorazmernye/*.csv row (confirmed against the folder's own
"Содержание папок и структура файлов.rtf" documentation, NOT just the
README's from-memory summary — the RTF is authoritative):

  col1 (source locus)   "<abbr>, [<book>, ]<chapter>: <absoluteChapter>"
  col2 (verse/pada)      "<verseInChapter> <padaInVerse>"  (pada always "1"
                         in this full-size/meter-to-meter export -- Stopovye
                         is where padaInVerse varies)
  col3 (source text)     the source pada/foot's text
  col4.. (repeated x4)   target_locus (self-describing full string, already
                         includes work name + book + chapter + verse + pada,
                         per the RTF -- stored VERBATIM, not re-decomposed),
                         target text, verdict (GOOD|PARTLY), word-diff
                         ("+ added - removed", empty when GOOD)

Filename: `<textNum>_<firstChapter>--<lastChapter>.csv` -- textNum indexes
the PARA export's OWN text list (`para_text_id_names.json`, extracted from
the RTF's "Список текстов Корпуса" section) -- CONFIRMED NOT the same
namespace as `dcs_full.sqlite.text.text_id` (spot check: PARA id 104 =
Divyāvadāna, but DCS text_id 104 is a different text; DCS text_ids run
1-579 over only 270 rows, non-contiguous). Do not join the two id spaces.

Emits:
  data/concordance/parallel_passage_concordance.tsv   one row per source-verse<->target link
  data/concordance/parallel_passage_verses.tsv         one row per source verse (incl. 0-parallel)
  data/concordance/PARALLEL_BUILD_REPORT.md            counts, honest caveats
  concordance/parallels/data/para_<textNum>.js         per-source-text shards for the static viewer
  concordance/parallels/data/_index.js                 text-picker index (id -> name, n_verses, n_linked)

Deterministic, no network, ~1-2 min over the 245-file / 57MB export.
"""
import collections
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concordance_core import RECORD_FIELDS  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
PARA_DIR = (GH / "VisualDCS" / "derived-data" / "Paralleli-v-tekstah-korpusa-SRC"
            / "PARA" / "Polnorazmernye")
NAMES_JSON = ROOT / "data" / "concordance" / "para_text_id_names.json"

OUT_DATA = ROOT / "data" / "concordance"
OUT_WEB = ROOT / "concordance" / "parallels" / "data"

SENT_TRUNC = 200
VERDICT_CONFIDENCE = {"GOOD": 0.95, "PARTLY": 0.55}
FNAME_RE = re.compile(r"^(\d+)_(.+)\.csv$")


def load_names():
    with open(NAMES_JSON, encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


def trunc(s, n=SENT_TRUNC):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + "…"


def parse_file(fp, text_id):
    """Yield (col1, col2, source_text, [(target_locus, target_text, verdict, diff), ...])."""
    with open(fp, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line:
                continue
            parts = line.split(";")
            if len(parts) < 3:
                continue
            col1, col2, src_text = parts[0], parts[1], parts[2]
            rest = parts[3:]
            n_groups = len(rest) // 4
            targets = []
            for i in range(n_groups):
                g = rest[i * 4:i * 4 + 4]
                if len(g) < 3:
                    continue
                tgt_locus, tgt_text = g[0], g[1]
                verdict = g[2]
                diff = g[3] if len(g) > 3 else ""
                if verdict not in ("GOOD", "PARTLY"):
                    continue
                targets.append((tgt_locus.strip(), tgt_text.strip(), verdict, diff.strip()))
            yield col1.strip(), col2.strip(), src_text.strip(), targets


def anchor_id(text_id, col1, col2):
    key = "%s|%s" % (col1, col2)
    return "para:%d:%s" % (text_id, key)


def main():
    names = load_names()
    files = sorted(glob.glob(str(PARA_DIR / "*.csv")))
    print("PARA_DIR:", PARA_DIR)
    print("n files:", len(files))
    if not files:
        print("ERROR: no CSV files found -- check the PARA_DIR path", file=sys.stderr)
        sys.exit(1)

    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_WEB.mkdir(parents=True, exist_ok=True)

    link_rows = []          # for the TSV (flat)
    verse_rows = []          # per-source-verse index rows
    shard_data = collections.defaultdict(dict)  # text_id -> {slug: {...}}
    text_stats = collections.OrderedDict()      # text_id -> [n_verses, n_linked, n_good, n_partly]
    seen_anchor_ids = set()
    dup_anchor_ids = 0
    n_verses_total = 0
    n_links_total = 0
    n_good_total = 0
    n_partly_total = 0
    file_missing_id = []

    for fp in files:
        fname = os.path.basename(fp)
        m = FNAME_RE.match(fname)
        if not m:
            file_missing_id.append(fname)
            continue
        text_id = int(m.group(1))
        chapter_range = m.group(2)
        text_name = names.get(text_id, "")
        stats = text_stats.setdefault(text_id, [0, 0, 0, 0])

        for col1, col2, src_text, targets in parse_file(fp, text_id):
            n_verses_total += 1
            stats[0] += 1
            aid = anchor_id(text_id, col1, col2)
            if aid in seen_anchor_ids:
                dup_anchor_ids += 1
            seen_anchor_ids.add(aid)

            n_good = sum(1 for t in targets if t[2] == "GOOD")
            n_partly = sum(1 for t in targets if t[2] == "PARTLY")
            verse_rows.append((
                aid, text_id, text_name, chapter_range, col1, col2,
                trunc(src_text), len(targets), n_good, n_partly,
            ))
            if targets:
                stats[1] += 1
                stats[2] += n_good
                stats[3] += n_partly
                n_links_total += len(targets)
                n_good_total += n_good
                n_partly_total += n_partly
                slug = "%s|%s" % (col1, col2)
                shard_data[text_id][slug] = {
                    "locus": col1, "vp": col2, "text": trunc(src_text),
                    "par": [
                        {"loc": tl, "txt": trunc(tt), "v": v, "d": d}
                        for tl, tt, v, d in targets
                    ],
                }
                for tl, tt, verdict, diff in targets:
                    link_rows.append((
                        aid, text_id, text_name, col1, col2, tl,
                        verdict, diff, VERDICT_CONFIDENCE[verdict],
                    ))

    print("source verses parsed: %d (across %d files)" % (n_verses_total, len(files)))
    print("verses with >=1 parallel: %d" % sum(s[1] for s in text_stats.values()))
    print("total links: %d (GOOD %d, PARTLY %d)" % (n_links_total, n_good_total, n_partly_total))
    if dup_anchor_ids:
        print("WARNING: %d duplicate anchor_ids (col1+col2 not unique within a file) -- "
              "later rows kept, see BUILD_REPORT" % dup_anchor_ids)
    if file_missing_id:
        print("WARNING: %d files did not match the naming pattern: %s"
              % (len(file_missing_id), file_missing_id[:5]))

    # ---- emit the concordance dataset (RECORD_FIELDS + extras) --------------
    ds = OUT_DATA / "parallel_passage_concordance.tsv"
    extra_fields = ["source_text_id", "source_text_name", "source_locus",
                     "source_verse_pada", "verdict", "word_diff"]
    with open(ds, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(RECORD_FIELDS + extra_fields) + "\n")
        for aid, text_id, text_name, col1, col2, tgt_locus, verdict, diff, conf in link_rows:
            f.write("\t".join([
                "parallel-verse", aid, "", tgt_locus, "dcs-parallel-passages-full",
                verdict, "%.2f" % conf, "1",
                str(text_id), text_name, col1, col2, verdict, diff,
            ]).replace("\n", " ") + "\n")

    # ---- per-source-verse index (coverage-style) -----------------------------
    vf = OUT_DATA / "parallel_passage_verses.tsv"
    with open(vf, "w", encoding="utf-8", newline="\n") as f:
        f.write("anchor_id\tsource_text_id\tsource_text_name\tchapter_range\t"
                "source_locus\tsource_verse_pada\tsource_text\tn_parallels\tn_good\tn_partly\n")
        for row in verse_rows:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in row) + "\n")

    # ---- web viewer shards ----------------------------------------------------
    index_entries = []
    total_bytes = 0
    for text_id, data in sorted(shard_data.items()):
        p = OUT_WEB / ("para_%d.js" % text_id)
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("window.PARA_DATA = window.PARA_DATA || {};\n")
            f.write('window.PARA_DATA[%d] = %s;\n' % (text_id, payload))
        total_bytes += p.stat().st_size
    for text_id, stats in sorted(text_stats.items()):
        index_entries.append({
            "id": text_id, "name": names.get(text_id, "(unnamed text %d)" % text_id),
            "n_verses": stats[0], "n_linked": stats[1],
            "n_good": stats[2], "n_partly": stats[3],
        })
    idx_p = OUT_WEB / "_index.js"
    with io.open(idx_p, "w", encoding="utf-8", newline="\n") as f:
        f.write("window.PARA_INDEX = ")
        f.write(json.dumps(index_entries, ensure_ascii=False, separators=(",", ":")))
        f.write(";\n")
    total_bytes += idx_p.stat().st_size
    print("web shards: %d text shards + index, %.1f MB total" % (len(shard_data), total_bytes / 1e6))

    # ---- build report -----------------------------------------------------------
    n_texts_with_data = len(text_stats)
    n_texts_linked = sum(1 for s in text_stats.values() if s[1] > 0)
    rep = OUT_DATA / "PARALLEL_BUILD_REPORT.md"
    with open(rep, "w", encoding="utf-8", newline="\n") as f:
        f.write("# parallel-passage-concordance (B3) -- build report\n\n")
        f.write("_Created: 13-07-2026 · Last updated: 13-07-2026_\n\n")
        f.write("Built by [scripts/build_parallel_passage_concordance.py]"
                "(https://github.com/gasyoun/kosha/blob/main/scripts/build_parallel_passage_concordance.py) "
                "(H836, Sonnet 5 `claude-sonnet-5`), from "
                "[VisualDCS/derived-data/Paralleli-v-tekstah-korpusa-SRC/PARA/Polnorazmernye/]"
                "(https://github.com/gasyoun/VisualDCS) "
                "(245 CSV files, the corrected/regenerated 2026 full-text-match pass).\n\n")
        f.write("## R-C2 -- canonical-variant decision (surfaced, not self-ruled)\n\n")
        f.write("Per `CONCORDANCE_ROADMAP.md` risk R-C2, this build used `Polnorazmernye/` "
                "(the 2026 full-size/meter-to-meter pass) as the working default -- the "
                "folder's *own* README already labels it “canonical” against "
                "`Polnorazmernye-2022-archive/` (“not canonical”, differs in 140/245 "
                "files per prior audit) and `Stopovye/` (a **different unit of comparison** "
                "-- per-pada/foot matching, not meter-to-meter, and only a partial 113-of-245-"
                "text run). This build does **not** independently re-content-diff the three "
                "variants row-by-row (no new evidence beyond the existing README audit) -- "
                "a human should confirm `Polnorazmernye/` as the released canonical before "
                "the dataset ships as \"final\", since the org convention is not to self-rule "
                "R-C2. `@DECIDE`: confirm `Polnorazmernye/` as canonical (or direct otherwise).\n\n")
        f.write("## Bloomfield RV cross-reference -- NOT built this pass\n\n")
        f.write("Roadmap Q2 asks for a Bloomfield *Vedic Concordance* (1906) pratika "
                "cross-reference for the RV subset. No digitization of Bloomfield's "
                "concordance was found anywhere in the org (checked: no repo under "
                "`GitHub/` mentions it outside this handoff and H731's bibliography note). "
                "Per roadmap open `@DECIDE` #3, which digitization to key against is a "
                "human call -- this is shipped as an honest gap, not fabricated. Once a "
                "source is chosen, the RV-subset rows in `parallel_passage_verses.tsv` "
                "(source_text_name matching the DCS Rgveda text) are ready to receive a "
                "`bloomfield_pratika` column in a follow-up pass.\n\n")
        f.write("## Counts\n\n")
        f.write("| metric | value |\n|---|---|\n")
        f.write("| source files (Polnorazmernye/*.csv) | %d |\n" % len(files))
        f.write("| source verses parsed | %d |\n" % n_verses_total)
        f.write("| source verses with >=1 parallel | %d (%.1f%%) |\n"
                 % (sum(s[1] for s in text_stats.values()), 100.0 * sum(s[1] for s in text_stats.values()) / max(n_verses_total, 1)))
        f.write("| total parallel links (GOOD+PARTLY) | %d |\n" % n_links_total)
        f.write("| — GOOD (exact) | %d |\n" % n_good_total)
        f.write("| — PARTLY (partial, word-diff attached) | %d |\n" % n_partly_total)
        f.write("| distinct source texts represented | %d |\n" % n_texts_with_data)
        f.write("| source texts with >=1 linked verse | %d |\n" % n_texts_linked)
        f.write("| duplicate anchor_ids (col1+col2 collision within a file) | %d |\n\n" % dup_anchor_ids)
        f.write("**Note on the roadmap's prior “506,787 alignments” estimate:** that figure "
                "(from `CONCORDANCE_ROADMAP.md`, sourced from the export's own README, which "
                "itself states it was “not independently sampled”) does not match this "
                "build's directly-parsed counts (%d source verses / %d actual GOOD+PARTLY "
                "links). This build's numbers come from parsing every row of every "
                "`Polnorazmernye/*.csv` file directly and are the authoritative count going "
                "forward; the discrepancy is flagged here rather than silently reconciled.\n\n"
                % (n_verses_total, n_links_total))
        f.write("## Schema notes (confirmed against the folder's own RTF documentation)\n\n")
        f.write("- `target_locus` is stored **verbatim** from column 4 of the source CSV -- "
                "the RTF states this column already IS the full self-describing locus "
                "(work name + book + chapter + verse + pada), so it is not re-decomposed.\n")
        f.write("- `anchor_id` = `para:<textId>:<col1>|<col2>` -- a synthetic but stable key "
                "combining the source PARA text id (own namespace -- **confirmed NOT the "
                "same as `dcs_full.sqlite.text.text_id`**, spot-checked on ids 104/107/10) "
                "with the verse/pada locus columns.\n")
        f.write("- `match_method` carries the source verdict (`GOOD`/`PARTLY`) directly, "
                "rather than the Q1 SLP1-tier vocabulary (`exact`/`floor`/`relaxed`/`fuzzy`) "
                "-- these are a different axis (textual-parallel-quality, not lexical-match-"
                "confidence) and deliberately not conflated. `confidence` maps GOOD=0.95, "
                "PARTLY=0.55 for cross-concordance sortability.\n\n")
        f.write("\n_Dr. Mārcis Gasūns_\n")

    print("dataset:", ds)
    print("verses index:", vf)
    print("report:", rep)


if __name__ == "__main__":
    main()
