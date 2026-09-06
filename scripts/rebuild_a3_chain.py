#!/usr/bin/env python
"""Re-run the whole A3 chain in order, capturing before/after numbers.

Every stage below reads `form_key()`, so the sanskrit-util 0.11.0 final-nasal fix
(`rasaṃ` and `rasam` finally share a key) invalidates all of them at once. Running them
piecemeal would leave the page and the triage keyed on one era and the audit on another —
which is the exact drift the A3 audit exists to catch.

Order is load-bearing: each stage consumes the previous one's output.

  1 build_morphology_attestation_audit_inflections.py   the expensive join (~27 min)
  2 analyze_morph_giveback_set.py                       narrows A¬G to candidates
  3 triage_morph_giveback_candidates.py                 cell-resolved verdicts
  4 _gen_giveback_validation_sheet.py                   the 40-card human sheet
  5 build_morphology_concordance_page.py                the web viewer (~25 min)

Refuses to start unless the library actually carries the fix — a stale sanskrit-util
checkout would silently reproduce the old keys and the whole run would be a no-op that
looks like a success.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def _github_root(root):
    env = os.environ.get("GITHUB_ROOT")
    if env:
        return Path(env)
    for cand in (root.parent, root.parent / "GitHub", root.parent.parent,
                 root.parent.parent / "GitHub"):
        if (cand / "sanskrit-util").is_dir() and (cand / "VisualDCS").is_dir():
            return cand
    sys.exit("cannot locate the GitHub org root; set GITHUB_ROOT")


GH = _github_root(ROOT)
sys.path.insert(0, str(GH / "sanskrit-util" / "py"))
import sanskrit_util as su  # noqa: E402

# --- precondition: the fix must be live in the library these scripts will import --------
# Each row is (must_be_equal, left, right, why). Both halves matter: the EQUAL rows prove the
# fold actually landed, the DISTINCT rows prove it did not land too wide. A stale checkout
# fails an EQUAL row; an over-eager reimplementation fails a DISTINCT row. Add a row here in
# the same pass as any further narrowing of form_key — this list is the only thing standing
# between a consumer and an hour-long rebuild that silently reproduces the previous era's keys.
INVARIANTS = [
    # H3911 — word-final anusvāra is /m/
    (True, "rasaṃ", "rasam", "final anusvāra folds to m (>=0.11.0)"),
    (False, "rājan", "rājam", "final -n is NOT merged into final -m"),
    # H3975 — medial anusvāra before a labial (p ph b bh m) is /m/ too
    (True, "saṃbhavaḥ", "sambhavaḥ", "medial anusvāra before a labial folds to m (>=0.12.0)"),
    (True, "vaiśaṃpāyana", "vaiśampāyana", "same, on the highest-evidence twin in the corpus"),
    (False, "saṃvatsara", "samvatsara", "v is not a labial stop — that anusvāra stays n"),
    (True, "saṃskṛta", "sanskṛta", "anusvāra before a non-labial still folds to n"),
]
_bad = []
for want_equal, left, right, why in INVARIANTS:
    if (su.form_key(left) == su.form_key(right)) is not want_equal:
        _bad.append("  %s %s %s   (form_key: %r vs %r)  -- %s"
                    % (left, "==" if want_equal else "!=", right,
                       su.form_key(left), su.form_key(right), why))
if _bad:
    sys.exit("REFUSING: %s does not carry the form_key contract this chain is keyed on.\n%s\n"
             "Update the sanskrit-util checkout to >=0.12.0 (and reinstall it if the consumer "
             "imports the installed package rather than the sibling checkout) before rebuilding."
             % (su.__file__, "\n".join(_bad)))
print("precondition OK: sanskrit_util %s at %s (%d form_key invariants)"
      % (getattr(su, "__version__", "?"), su.__file__, len(INVARIANTS)), flush=True)

STAGES = [
    ("audit  ", ["scripts/build_morphology_attestation_audit_inflections.py"]),
    ("narrow ", ["scripts/analyze_morph_giveback_set.py"]),
    ("triage ", ["scripts/triage_morph_giveback_candidates.py"]),
    ("sheet  ", ["scripts/_gen_giveback_validation_sheet.py",
                 "review/kosha-giveback-slot-conflicts_h3863_review.html"]),
    ("page   ", ["scripts/build_morphology_concordance_page.py", "--coverage", "0.95"]),
]


def main():
    if "--check" in sys.argv[1:]:
        # The invariant block above already ran (and exited non-zero on any failure), so
        # reaching here IS the pass. Exists so a consumer can prove its checkout before
        # committing to a ~55-minute rebuild, instead of learning at minute 54.
        for want_equal, left, right, why in INVARIANTS:
            print("  %-14s %s %-14s  -> %-14r  %s"
                  % (left, "==" if want_equal else "!=", right, su.form_key(left), why))
        return
    (ROOT / "review").mkdir(exist_ok=True)
    t0 = time.time()
    for name, args in STAGES:
        t = time.time()
        print("\n=== %s START %s ===" % (name.strip(), " ".join(args)), flush=True)
        r = subprocess.run([sys.executable] + args, cwd=str(ROOT),
                           capture_output=True, text=True, encoding="utf-8")
        tail = [ln for ln in (r.stdout or "").strip().split("\n") if ln][-4:]
        for ln in tail:
            print("   %s" % ln, flush=True)
        if r.returncode != 0:
            err = (r.stderr or "").strip().split("\n")[-12:]
            print("   STDERR:\n     %s" % "\n     ".join(err), flush=True)
            sys.exit("STAGE FAILED: %s (exit %d) after %.0fs"
                     % (name.strip(), r.returncode, time.time() - t))
        print("=== %s OK  %.0fs ===" % (name.strip(), time.time() - t), flush=True)
    print("\nALL STAGES OK in %.0f s (%.1f min)"
          % (time.time() - t0, (time.time() - t0) / 60), flush=True)


if __name__ == "__main__":
    main()
