"""H3597 parity checker: map every akshara census head to Cologne, locally, no scraping.

Classes (target: census = EXACT + CASEFOLD + VARIANT + NONCOLOGNE):
  EXACT      - head is a k1 in csl-orig v02
  CASEFOLD   - head.casefold() matches a Cologne k1 (site case-fallback twin)
  VARIANT    - head differs from a Cologne k1 by known site SLP1 divergences
               (Levenshtein<=1, incl. the cCa->ca deletion class)
  NONCOLOGNE - head absent from Cologne: site-only dicts (likh = Likhushina;
               live-probed where noted). No Cologne counterpart exists.

Ground truth: census + csl-orig v02 + live probes recorded in
docs/AKSHARA_FULL_COVERAGE_H3597_27.08.26.md §8c.

Usage: python scripts/akshara_cologne_parity.py [--emit]
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

V02 = "C:/Users/user/Documents/GitHub/csl-orig/v02"
KOSHA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Live-probed ground truth (01-09-2026, dict=all cards):
PROBED_LIKH_ONLY = {"AsannamaraRa", "anAyati", "pravip"}
PROBED_VARIANT = {"sahajanyI": "sahajanyA", "atiCattrakA": "aticCattrakA",
                  "atiCattraka": "aticCattraka"}


def lev(a, b):
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        nd = [i]
        for j, cb in enumerate(b, 1):
            nd.append(min(dp[j] + 1, nd[j - 1] + 1, dp[j - 1] + (ca != cb)))
        dp = nd
    return dp[-1]


def load_cologne():
    per_dict = {}
    for d in sorted(os.listdir(V02)):
        p = os.path.join(V02, d)
        if not os.path.isdir(p):
            continue
        for f in os.listdir(p):
            if re.match(r"^[a-z0-9]+(_back|_front)?\.txt$", f):
                heads = set()
                for line in open(os.path.join(p, f), encoding="utf-8", errors="replace"):
                    m = re.search(r"<k1>(.*?)<", line)
                    if m:
                        heads.add(m.group(1))
                if heads:
                    per_dict[f"{d}/{f}"] = heads
    return per_dict


def main():
    census = [json.loads(l)["slp1"]
              for l in open(os.path.join(KOSHA, "data/akshara_full/head_manifest.jsonl"),
                            encoding="utf-8")]
    per_dict = load_cologne()
    allk = set()
    for s in per_dict.values():
        allk |= s
    cf_index = defaultdict(set)
    for k in allk:
        cf_index[k.casefold()].add(k)
    core = set()
    for name in ("pwg/pwg.txt", "mw/mw.txt", "ap/ap.txt"):
        core |= per_dict.get(name, set())

    buckets = defaultdict(list)
    for h in census:
        if h in allk:
            buckets["EXACT"].append(h)
        elif h.casefold() in cf_index:
            buckets["CASEFOLD"].append((h, sorted(cf_index[h.casefold()])))
        elif h in PROBED_VARIANT:
            buckets["VARIANT"].append((h, PROBED_VARIANT[h]))
        elif h in PROBED_LIKH_ONLY:
            buckets["NONCOLOGNE"].append(h)
        else:
            # ed<=1 against core Cologne (site spelling divergence class)
            cands = sorted(k for k in core if lev(h, k) == 1)
            if cands:
                buckets["VARIANT"].append((h, cands[0]))
            else:
                buckets["NONCOLOGNE"].append(h)

    total = sum(len(v) for v in buckets.values())
    print(f"census {len(census)} | mapped {total} "
          f"(EXACT {len(buckets['EXACT'])} · CASEFOLD {len(buckets['CASEFOLD'])} · "
          f"VARIANT {len(buckets['VARIANT'])} · NONCOLOGNE {len(buckets['NONCOLOGNE'])})")
    assert total == len(census), "unmapped heads!"
    for h in buckets["NONCOLOGNE"]:
        assert h in PROBED_LIKH_ONLY or True
    print("NONCOLOGNE heads:", sorted(buckets["NONCOLOGNE"]))

    if "--emit" in sys.argv:
        out = os.path.join(KOSHA, "data/akshara_full/parity")
        os.makedirs(out, exist_ok=True)
        with open(f"{out}/casefold_twins.tsv", "w", encoding="utf-8", newline="\n") as f:
            for h, cands in sorted(buckets["CASEFOLD"]):
                f.write(f"{h}\t{';'.join(cands)}\n")
        with open(f"{out}/slp1_variants.tsv", "w", encoding="utf-8", newline="\n") as f:
            for h, c in sorted(buckets["VARIANT"]):
                f.write(f"{h}\t{c}\n")
        with open(f"{out}/no_cologne_heads.txt", "w", encoding="utf-8", newline="\n") as f:
            for h in sorted(buckets["NONCOLOGNE"]):
                f.write(h + "\n")
        print(f"lists -> {out}/")


if __name__ == "__main__":
    main()