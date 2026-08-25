"""ls_census_h3479.py — H3479 census: `<ls>` literary-source citations on the
H3457 staged sample, by resolution class (scan-wired campaign / e-text /
mintable / no-locus). PWG only (MW-side is a later wave)."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from word_page import entry_fields, card_token  # noqa: E402
from ls_hydrate import census_pwg_ls  # noqa: E402

LEMMAS = ["kf", "gam", "vac", "as", "deva", "Darma", "agni", "rAma", "jana", "nf", "yA"]


def main():
    lines = ["| lemma | pwg entries | `<ls>` total | scan_wired | e-text | mintable | no_locus |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    total = Counter()
    for lemma in LEMMAS:
        tok = card_token(lemma)
        card = json.loads((ROOT / "docs" / "cards" / f"{tok}.json").read_text(encoding="utf-8"))
        pwg = [r for r in card["results"] if entry_fields(r).get("dict") == "pwg"]
        stats = Counter()
        for r in pwg:
            stats.update(census_pwg_ls(entry_fields(r).get("rendered_html", "")))
        n = sum(stats.values())
        lines.append(f"| `{lemma}` | {len(pwg)} | {n} | {stats.get('hit_scan', 0)} | "
                     f"{stats.get('hit_etext', 0)} | {stats.get('mintable', 0)} | "
                     f"{stats.get('no_locus', 0)} |")
        total.update(stats)
    n_total = sum(total.values())
    lines.append(f"| **all 11** | — | **{n_total}** | **{total.get('hit_scan', 0)}** | "
                 f"**{total.get('hit_etext', 0)}** | **{total.get('mintable', 0)}** | "
                 f"**{total.get('no_locus', 0)}** |")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
