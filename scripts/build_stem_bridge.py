"""kosha P4 Wave K2a (H181) -- stem-normalization bridge between the two
form->lemma layers.

`inflections` (Cologne csl-inflect, case/number-labeled) and `forms`
(DCS/vidyut/heritage, lemma-only) cite the SAME lexeme under different stem
spellings. The classic mismatch is the strong/weak nasal stem: DCS records the
strong stem `Bagavant` while csl-inflect declines the weak stem `Bagavat` --
so a single query for the surface form `BagavAn` otherwise returns two
"different" lemmas for one word. This crosswalk maps each variant spelling to
ONE canonical lemma key so the reverse-lookup pipeline (app/reverse_lookup.py)
surfaces a unified answer.

Normalization rule (deliberately narrow, and DATA-GATED so unrelated
homographs are never merged): a pair (strong, weak) is bridged only when BOTH

  1. `strong` reduces to `weak` under a whitelisted morphophonemic collapse:
        -ant / -vant / -mant  ->  -at / -vat / -mat   (nasal cluster: nt -> t)
        -an  / -van  / -man   ->  -a  / -va  / -ma     (drop stem-final n)
     (the -in -> -i drop is deliberately NOT included: -in stems cite as -in in
     both layers, so collapsing them would merge genuinely distinct i-stems.)
  2. `strong` and `weak` actually SHARE at least one surface form across the
     two tables (e.g. both inflect to `BagavAn`).

Canonical = the weak stem (the traditional dictionary-citation form and the
csl-inflect spelling). Every strong variant maps to it; the weak form also maps
to itself, so a lookup can canonicalize any lemma with one dict hit.

    python scripts/build_stem_bridge.py            # uses data/db/kosha.db
Requires `inflections` and `forms` to be populated first.
"""
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent


def weak_variants(stem: str):
    """Yield the whitelisted weak-stem spelling(s) of a (strong) stem."""
    out = []
    if stem.endswith("nt") and len(stem) > 2:
        out.append(stem[:-2] + "t")      # -ant/-vant/-mant -> -at/-vat/-mat
    if stem.endswith("an") and len(stem) > 2:
        out.append(stem[:-1])            # -an/-van/-man -> -a/-va/-ma
    return out


def build_stem_bridge(con: sqlite3.Connection):
    con.execute("DELETE FROM stem_bridge")
    con.commit()

    inf_lemmas = {r[0] for r in con.execute("SELECT DISTINCT lemma_slp1 FROM inflections")}
    form_lemmas = {r[0] for r in con.execute("SELECT DISTINCT lemma_slp1 FROM forms")}
    all_lemmas = inf_lemmas | form_lemmas

    def forms_of(lemma):
        s = {r[0] for r in con.execute(
            "SELECT form_slp1 FROM inflections WHERE lemma_slp1=?", (lemma,))}
        s |= {r[0] for r in con.execute(
            "SELECT form_slp1 FROM forms WHERE lemma_slp1=?", (lemma,))}
        return s

    pairs = {}  # variant_slp1 -> (canonical_slp1, rule)
    canonicals = set()
    for strong in all_lemmas:
        for weak in weak_variants(strong):
            if weak == strong or weak not in all_lemmas:
                continue
            # data gate: the two spellings must genuinely share a surface form.
            if forms_of(strong) & forms_of(weak):
                rule = "nasal_cluster_nt_t" if strong.endswith("nt") else "drop_final_n"
                pairs[strong] = (weak, rule)
                canonicals.add(weak)

    rows = [(v, c, rule) for v, (c, rule) in pairs.items()]
    # the canonical weak stems also map to themselves, so a single lookup
    # canonicalizes any lemma (strong -> weak, weak -> weak).
    rows += [(c, c, "identity") for c in canonicals if c not in pairs]
    con.executemany(
        "INSERT OR REPLACE INTO stem_bridge (variant_slp1, canonical_slp1, rule) VALUES (?,?,?)",
        rows,
    )
    con.commit()

    n_variants = len(pairs)
    n_groups = len(canonicals)
    print(f"[P4 K2a] stem_bridge: {n_variants} strong->weak variant mappings "
          f"across {n_groups} canonical stems ({len(rows)} rows incl. identity). "
          f"Rule: nt->t / drop-final-n, gated on shared surface form.")
    # Named exit example (H181 deliverable 2): Bagavant must canonicalize to Bagavat.
    chk = con.execute(
        "SELECT canonical_slp1 FROM stem_bridge WHERE variant_slp1='Bagavant'").fetchone()
    print(f"    exit check: Bagavant -> {chk[0] if chk else 'MISSING'}")
    return n_variants


if __name__ == "__main__":
    con = sqlite3.connect(str(ROOT / "data" / "db" / "kosha.db"))
    build_stem_bridge(con)
    con.close()
