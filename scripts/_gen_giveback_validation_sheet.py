#!/usr/bin/env python
"""Validation sheet for the csl-inflect give-back slot-conflicts (H3863).

The triage resolved 5,655 of 5,656 candidates mechanically, so **the candidate set itself
is not sheet material** — a card the machine has answered does not belong on a human's
plate (the emitter enforces exactly this: `non_decision_share` defaults to 0.0).

What IS judgment: before 5,149 rows are handed to a third-party project, someone should
confirm the *method* is sound on the class where the machine's verdict is a claim about
Sanskrit rather than a lookup. That class is **slot-conflict** — the generator has the
`(lemma, gender, case, number)` slot and emits a *different* form from the one the corpus
attests. Deciding which is right is philology, not a join.

So this sheet is a **sample of 40 slot-conflicts, highest-attestation first**, not the
2,441. Approving them says "the corpus form is a real cell the generator should produce";
rejecting says "the generator is right, or this is not a gap". A high reject rate would
invalidate the method before anything reaches csl-inflect, which is the point of running
it first.

Emitted through the canonical `csl_pyutil.render_review_sheet` (V1–V8 standard), never
hand-rolled HTML.
"""
import argparse
import collections
import csv
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _github_root(root):
    env = os.environ.get("GITHUB_ROOT")
    if env:
        return Path(env)
    for cand in (root.parent, root.parent / "GitHub", root.parent.parent,
                 root.parent.parent / "GitHub"):
        if (cand / "VisualDCS").is_dir():
            return cand
    sys.exit("cannot locate the GitHub org root; set GITHUB_ROOT")


GH = _github_root(ROOT)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from csl_pyutil import render_review_sheet  # noqa: E402

DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
TRIAGED = ROOT / "data" / "concordance" / "morph_giveback_triaged.tsv"
SHEET_ID = "kosha-giveback-slot-conflicts_h3863"
N_CARDS = 40
CASE_EN = {"nom": "nominative", "acc": "accusative", "instr": "instrumental",
           "dat": "dative", "abl": "ablative", "gen": "genitive", "loc": "locative",
           "voc": "vocative"}
NUM_EN = {"sg": "singular", "du": "dual", "pl": "plural"}
GEN_EN = {"m": "masculine", "n": "neuter", "f": "feminine"}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="output .html path")
    ap.add_argument("--cards", type=int, default=N_CARDS)
    args = ap.parse_args()

    rows = []
    total = 0
    verdicts = collections.Counter()
    with TRIAGED.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            total += 1
            verdicts[r["verdict"]] += 1
            if r["verdict"] == "slot-conflict":
                rows.append(r)
    rows.sort(key=lambda x: -int(x["evidence_count"]))
    picked = rows[:args.cards]

    # one KWIC line per card, plus the human locus behind each `dcs:<sent_id>`.
    # The bare id is exactly the V13 identity problem: a reviewer cannot tell which text
    # `dcs:479312` is, so it is resolved to "Text, chapter-ref, sentence" here and the
    # mapping is handed to the identity gate rather than the warning being acknowledged.
    wanted = {r["target_locus"].split(":", 1)[1] for r in picked}
    sents, human_loci = {}, {}
    if DCS.exists():
        con = sqlite3.connect("file:%s?mode=ro" % DCS.as_posix(), uri=True)
        for sid, text in con.execute("SELECT sent_id, text_sandhied FROM sentence"):
            if sid in wanted and text:
                t = text.strip()
                sents[sid] = (t[:220] + "…") if len(t) > 220 else t
        for sid, tname, ref, cnt in con.execute(
                "SELECT s.sent_id, x.name, c.ref, s.sent_counter FROM sentence s "
                "JOIN chapter c ON c.chapter_id = s.chapter_id "
                "JOIN text x ON x.text_id = c.text_id"):
            if sid in wanted:
                # a null sent_counter must not render as the literal "None"
                parts = [p for p in (tname, ref, cnt) if p not in (None, "", "None")]
                human_loci["dcs:%s" % sid] = ", ".join(str(p) for p in parts)
        con.close()

    items = []
    for r in picked:
        g, c, n = (r["cell"].split(".") + ["", "", ""])[:3]
        cell_en = "%s %s %s" % (GEN_EN.get(g, g), CASE_EN.get(c, c), NUM_EN.get(n, n))
        sid = r["target_locus"].split(":", 1)[1]
        kwic = sents.get(sid, "")
        panels = [
            ("The disagreement",
             "<p><b>Corpus attests</b> <code>%s</code> &nbsp;·&nbsp; "
             "<b>generator emits</b> <code>%s</code></p>"
             "<p>Same cell: <b>%s</b> of <code>%s</code>. The corpus form occurs "
             "<b>%s</b> times; the generator does not produce it anywhere.</p>"
             % (esc(r["attested_form"]), esc(r["generator_has"]), esc(cell_en),
                esc(r["dcs_lemma"]), "{:,}".format(int(r["evidence_count"])))),
        ]
        if kwic:
            panels.append(("Corpus evidence",
                           "<p style='font-size:15px'>%s</p>"
                           "<p style='color:#667;font-size:12px'>%s — locus "
                           "<code>%s</code>, DCS's own stable sentence id, resolvable "
                           "offline against any copy of the corpus</p>"
                           % (esc(kwic),
                              esc(human_loci.get(r["target_locus"], "text unresolved")),
                              esc(r["target_locus"]))))
        panels.append((
            "What your vote does",
            "<p><b>Approve</b> — the corpus form is a real paradigm cell the generator "
            "should produce; this row ships to the csl-inflect give-back.<br>"
            "<b>Reject</b> — the generator is right, or this is not a missing cell "
            "(a sandhi/orthographic variant, a mis-lemmatisation, a compound member).<br>"
            "<b>Defer</b> — undecided.</p>"
            "<p style='color:#667;font-size:12px'>This is a <b>sample of %s</b> "
            "slot-conflicts, not the whole set. A high reject rate invalidates the "
            "method before anything reaches csl-inflect — which is why it runs first.</p>"
            % "{:,}".format(verdicts["slot-conflict"])))
        items.append({
            "id": "sc-%s" % r["attested_form"],
            "filt": CASE_EN.get(c, "other"),
            "title": "%s  vs  %s   (%s)" % (r["attested_form"], r["generator_has"], cell_en),
            "badges": [r["dcs_lemma"], "%s×" % "{:,}".format(int(r["evidence_count"])),
                       r["dcs_upos"]],
            "question": "Is <code>%s</code> a paradigm cell the generator should produce "
                        "for <code>%s</code>?" % (esc(r["attested_form"]),
                                                  esc(r["dcs_lemma"])),
            "panels": panels,
            "note_placeholder": "e.g. 'variant, not a gap' / 'yes, strī has both'",
        })

    filters = sorted({i["filt"] for i in items})
    config = {
        "sheet_id": SHEET_ID,
        "title": "csl-inflect give-back — slot-conflict validation (kosha A3)",
        "subtitle": ("%d of %s slot-conflicts, highest-attestation first. In each, the "
                     "corpus and the generator disagree about the SAME paradigm cell. "
                     "Approving ships the row upstream; a high reject rate stops the "
                     "hand-off. The other %s triaged rows are machine-resolved and are "
                     "deliberately NOT on this sheet."
                     % (len(items), "{:,}".format(verdicts["slot-conflict"]),
                        "{:,}".format(total - verdicts["slot-conflict"]))),
        "footer": ("Source: data/concordance/morph_giveback_triaged.tsv (H3863) over "
                   "morph_giveback_candidates.tsv (H3782). Cells from DCS feat_case/"
                   "feat_number/feat_gender; generator forms from kosha.db inflections. "
                   "Loci are host-independent dcs:&lt;sent_id&gt;."),
        "approve_label": "Real gap — ship it",
        "reject_label": "Not a gap",
        "filters": [(f, f) for f in filters],
        "generated": time.strftime("%d-%m-%Y"),
        # V13: every `dcs:<sent_id>` a card shows is paired with the text it names, so no
        # reviewer is asked to vote against an opaque internal id.
        "identity_gate": {
            "patterns": [r"dcs:\d+(?:_\d+)?"],
            "labels": human_loci,
        },
    }
    screening = {
        "deterministic": total - verdicts["slot-conflict"],
        "lookup": 0,
        "agent": 0,
        "human": len(items),
        "evidence_path": "data/concordance/MORPHOLOGY_GIVEBACK_TRIAGE_REPORT.md",
        "rules": [
            "DCS feat_case='Cpd' -> compound member, not an inflected cell (222 rows)",
            "caseless + upos ADV/SCONJ/PART/ADP -> indeclinable, not owed (33 rows)",
            "final anusvara spelling of a form the generator already emits -> "
            "orthographic variant, not a gap (146 rows)",
            "real case+number and the generator's slot is EMPTY -> coverage-hole, owed "
            "with no adjudication needed (2,708 rows)",
            "real case+number and the generator emits a DIFFERENT form -> slot-conflict: "
            "the only class whose verdict is a claim about Sanskrit, sampled here",
        ],
    }
    html = render_review_sheet(items, config, screening=screening)
    Path(args.out).write_text(html, encoding="utf-8")
    print("wrote %s — %d cards (of %s slot-conflicts; %s rows machine-resolved)"
          % (args.out, len(items), "{:,}".format(verdicts["slot-conflict"]),
             "{:,}".format(total - verdicts["slot-conflict"])))


if __name__ == "__main__":
    main()
