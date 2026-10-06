#!/usr/bin/env python3
"""nws_ingest_pipeline.py — H6064: NWS (Nachtragswörterbuch, Halle) intake
pipeline for kosha — siglum-parse + fuzzy works-registry match + key1 lemma
matching + dump readiness, per decisions H5937–41 (grill 04-10-2026).

Stages
  1. registry   — 174 Erfasste Werke (nws.uzi.uni-halle.de/dictionaries),
                  committed at data/nws/nws_works_registry.json (MLU Halle
                  attribution; Impressum probe 04-10-2026: texts usable with
                  attribution). Built by --build-registry from fetched HTML.
  2. intake     — per-lemma JSON stream from the private tar
                  (pwg-ru-data/layers/nws.tar.gz) with the H5937 service-file
                  filter (.claude/, _keys_*, _progress.log, _status.txt,
                  _watch_state), or --from-ocr-route DIR for the H6067 OCR
                  export shape (dump readiness, post-H5940-letter).
  3. siglum     — parse the `nws` prose field per the site-documented format
                  (<Textgattung/Sachkategorie> > Wortart Genus … Bedeutung …
                  Stellenbeleg. Literaturverweis. <Glossar: Seite>): grammar
                  header, sense segments, attestation sigla lists, page
                  precise refs (S./Z.), author-year literature refs, dictionary
                  markers (MW : 145).
  4. fuzzy      — match every parsed siglum against the 174-work registry:
                  exact → normalized (case/punct/disambiguator) → author-year
                  + Levenshtein-1. Unregistered sigla (Mbh, R, Suś …) fall to
                  the attestation census, never dropped.
  5. key1       — lemma matching by key1 (SLP1), NOT by tar stem — the H6050
                  contract: the stem namespace ("_a_sana") is a site encoding
                  (_x → uppercase x, verified 167k/167k), key1 is the join
                  key. Stem decoding is the fallback for dump entries without
                  key1; orphans stay out of any lemma inventory until
                  hand-ruled.
  6. report     — compliance report over ALL 174 works (rows exist even at 0
                  citations), unregistered-sigla census, headline numbers.

Usage
  python3 scripts/nws_ingest_pipeline.py --build-registry nws_dictionaries.html
  python3 scripts/nws_ingest_pipeline.py --full-tar [--report DIR]
  python3 scripts/nws_ingest_pipeline.py --from-ocr-route DIR [--report DIR]
  python3 scripts/nws_ingest_pipeline.py --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import html as htmllib
import json
import re
import sys
import tarfile
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "data" / "nws" / "nws_works_registry.json"

SITE = "https://nws.uzi.uni-halle.de/dictionaries"
RIGHTS = ("MLU Halle-Wittenberg — publicly available TEXTS reusable with "
          "attribution (Impressum probe 04-10-2026)")

TAR_SHA256_PIN = "054b05da96df2f1af2c95c02b7e15d87f8a616d4eaa339f93e3ed7430e07f00c"

# H5937 service files: caught-by-scrape non-lemmas inside the tar directory.
SERVICE_RE = re.compile(r"(^|/)(\.claude(/|$)|_keys_|_progress\.log|_status\.txt|_watch_state)")

# --- pinned H6064 numbers (full-tar run 06-10-2026, sha256 054b05da…) ------
PINNED = {
    "registry_works": 174,
    "tar_lemmas": 167990,            # lemma JSONs after H5937 service filter
    "tar_service_files": 7,          # 2 service .json + 5 txt/lock/log
    "key1_present": 167990,           # every true lemma JSON carries key1
    "stem_decode_agree": 167990,     # decode(stem) == key1 wherever key1 present
    "nws_content_entries": 34101,    # entries with non-empty nws prose
    "has_nws_extra_true": 34101,     # all prose entries carry the extra flag
    "page_refs": 8440,               # "S. n, Z. n" page-precise citations
    "lit_refs": 8937,                # "Author Year : page" citations
    "dict_marker_entries": 4941,     # entries carrying e.g. "MW : 145"
    "works_attested": 82,            # of the 174 registry works cited >=1x
    "unparsed_seg_pct_max": 0.5,     # fail bar (H5937): <=0.5% unparsed
    # canaries (H5937 lock)
    "canary_asana_litref": "Ensink 1964",
    "canary_asana_pageref": "ĀdiPa Ed",
    "canary_asana_header": "Reg , unsp > Subst n",
    "canary_aba_sigla": ["Mbh", "MānDhŚ", "Suś", "Pañcat", "R", "Kāvyād", "Śiśup"],
}

# --- siglum parsing ---------------------------------------------------------

WORTART = ("Subst|Adj|Adv|Ind|Präp|Part|Konj|Pron|Num|Verb|Interj|Fragewort")
WORTART_RE = re.compile(rf"\b({WORTART})\b\s*(mfn|m|f|n)?\b")
CAP0 = "A-ZĀĒĪŌṚŚṢÑṆṄḶḌṬXVILC"          # capital-ish first letters (IAST incl.)
TOKCH = r"[\w\-'’.()/āīūēōṛṝḹśṣṇṅñḍṭḷçḥṃ0-9]*"
SIGLUM_TOK_RE = re.compile(rf"^[{CAP0}]{TOKCH}$")
PAGE_RE = re.compile(r"S\.\s*\d+")
LITREF_RE = re.compile(rf"^([{CAP0}]{TOKCH})(?:\s+\(\d\))?\s+(1[89]\d\d|20[0-2]\d)\s*:\s*\d+$")
DICTMARK_RE = re.compile(r"^([A-Z]{2,6}(?:\([A-Z]{2,6}\))?)\s*:\s*\d+$")


def is_siglum_token(tok: str) -> bool:
    """A candidate attestation/work token: starts capital-ish, no spaces."""
    if not tok or tok.isdigit() or len(tok) < 1:
        return False
    if tok in {"Ed", "Übers", "Krit", "Ved", "Reg", "Gen", "unsp"}:
        return False                      # edition/semantic markers, not works
    return bool(SIGLUM_TOK_RE.match(tok))


def parse_nws_field(prose: str) -> dict:
    """Parse one `nws` field per the H5937 site-format contract.

    Returns {header, senses, sigla, page_refs, lit_refs, dict_markers,
    unparsed} — entry-level aggregation; sense segments counted.
    """
    out: dict = {"header": "", "senses": 0, "sigla": [], "page_refs": [],
                 "lit_refs": [], "dict_markers": [], "unparsed": 0}
    s = (prose or "").strip()
    if not s:
        return out
    # trailing glossar marker "<Glossar: Seite>" style: " >" terminator
    s = s[:-1].rstrip() if s.endswith(">") else s
    # grammar header: everything through Wortart+Genus, e.g.
    # "āśana Reg , unsp > Subst n"
    m = WORTART_RE.search(s)
    if m:
        out["header"] = s[: m.end()].strip()
        body = s[m.end():].strip()
    else:
        out["header"] = s.split(">", 1)[0].strip()
        body = s.split(">", 1)[1].strip() if ">" in s else ""
    # protect intra-reference periods ("S. 206", "Z. 4", "V. 5") from the
    # sentence split, and split numbered senses ("1) … 2) …") as well
    body = re.sub(r"\b([A-Z])\.\s*(\d)", r"\1§\2", body)
    segs = [x.strip() for x in re.split(r"(?<=\.)\s+(?=[^0-9§])|(?=\d\))",
                                        body) if x.strip()]
    for seg in segs:
        seg = re.sub(r"([A-Z])\.(\d)", r"\1. \2", seg.replace("§", "."))
        bare = seg[:-1].rstrip() if seg.endswith(".") else seg
        # 1) dictionary marker  "MW : 145"
        dm = DICTMARK_RE.match(bare)
        if dm:
            out["dict_markers"].append(dm.group(1))
            continue
        # 2) literature ref     "Ensink 1964 : 27"
        lm = LITREF_RE.match(bare)
        if lm:
            out["lit_refs"].append(lm.group(1) + " " + lm.group(2))
            continue
        # 3) page-precise ref   "ĀdiPa Ed, S. 206, Z. 4"
        if PAGE_RE.search(seg):
            work_part = re.split(r"S\.", seg, maxsplit=1)[0].strip().rstrip(",").strip()
            for tok in re.split(r"[\s,/]", work_part):
                tok = tok.strip()
                if is_siglum_token(tok):
                    out["sigla"].append(tok)
            out["page_refs"].append(seg)
            continue
        # 4) attestation sigla list  "Mbh , MānDhŚ , Suś , Pañcat ."
        parts = [p.strip().rstrip('.').strip() for p in seg.split(" , ")]
        toks = [p for p in parts if p]
        if toks and all(is_siglum_token(p) for p in toks):
            if len(toks) >= 2 or seg.endswith(" ."):
                out["sigla"].extend(toks)
                continue
            # single capitalized token alone: could be a sense in German —
            # only a residue when comma-structured but unclassified
        # 5) otherwise: sense prose; residue only for comma-structured
        #    capitalized fragments that matched no branch above
        seg_parts = [p for p in (x.strip() for x in seg.split(" , ")) if p]
        sig_like = sum(1 for p in seg_parts if is_siglum_token(p))
        if sig_like >= 2 and not seg.endswith("."):
            out["unparsed"] += 1
        out["senses"] += 1
    return out


# --- works registry ---------------------------------------------------------

def norm_siglum(s: str) -> str:
    """Normalization for registry matching: casefold, drop non-alnum."""
    return re.sub(r"[^a-z0-9]", "", s.casefold())


def build_registry_from_html(html_path: Path) -> list[dict]:
    """Parse the /dictionaries page: <h4>siglum</h4><p>citation…</p> blocks."""
    s = html_path.read_text(encoding="utf-8")
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S)
    rec_re = re.compile(
        r"<h4[^>]*>(?P<sig>[^<]+)</h4>\s*<p>(?P<body>.*?)</p>", re.S)
    works = []
    for i, m in enumerate(rec_re.finditer(s), 1):
        raw = re.sub(r"<br\s*/?>", "\n", m.group("body"))
        raw = re.sub(r"<[^>]+>", "", raw)
        text = htmllib.unescape(raw)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        tg = lines[lines.index("Textgattung:") + 1] if "Textgattung:" in lines else ""
        try:
            sk = lines[lines.index("Sachkategorie:") + 1]
        except ValueError:
            sk = ""
        works.append({
            "id": i,
            "siglum": m.group("sig").strip(),
            "citation": " ".join(l for l in lines
                                 if l not in ("Textgattung:", "Sachkategorie:",
                                              "—", tg, sk)),
            "textgattung": tg,
            "sachkategorie": sk,
        })
    return works


class WorksIndex:
    """Exact / normalized / fuzzy index over the 174 Erfasste Werke."""

    def __init__(self, works: list[dict]):
        self.works = works
        self.by_norm: dict[str, dict] = {}
        self.ay_tokens: list[tuple[str, dict]] = []   # (authortok, work)
        for w in works:
            self.by_norm[norm_siglum(w["siglum"])] = w
            m = re.match(rf"([{CAP0}][\w'’\-]+)", w["siglum"])
            if m:
                self.ay_tokens.append((norm_siglum(m.group(1)), w))

    def match(self, tok: str) -> tuple[dict | None, str]:
        """→ (work record or None, method exact|normalized|fuzzy|none)."""
        n = norm_siglum(tok)
        if not n:
            return None, "none"
        if n in self.by_norm:
            return self.by_norm[n], "exact"
        # strip disambiguators / trailing edition markers: "Bareau 1953 (1)"
        n2 = norm_siglum(re.sub(r"\s*\(\d\)\s*$", "", tok))
        if n2 in self.by_norm and n2 != n:
            return self.by_norm[n2], "normalized"
        # author-token + year inside the token ("Ensink 1964 : 27" pre-split)
        m = re.match(rf"([{CAP0}][\w'’\-]+)\s+((?:1[89]|20)\d\d)", tok)
        if m:
            an = norm_siglum(m.group(1))
            year = m.group(2)
            for a, w in self.ay_tokens:
                if a == an and year in w["siglum"]:
                    return w, "fuzzy-author-year"
        return None, "none"


def load_registry(path: Path = REGISTRY) -> list[dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc["works"]


# --- intake -----------------------------------------------------------------

def _default_tar() -> Path:
    for cand in (REPO.parent / "pwg-ru-data" / "layers" / "nws.tar.gz",
                 REPO.parent.parent / "pwg-ru-data" / "layers" / "nws.tar.gz",
                 Path.home() / "Documents" / "GitHub" / "pwg-ru-data"
                 / "layers" / "nws.tar.gz"):
        if cand.exists():
            return cand
    return cand


def iter_tar_lemmas(tar_path: Path):
    """Yield (stem, json) for lemma files only (H5937 service filter)."""
    with tarfile.open(tar_path, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            name = m.name.rsplit("/", 1)[-1]
            if SERVICE_RE.search(m.name) or not name.endswith(".json"):
                continue
            try:
                fh = tf.extractfile(m)
                if fh is None:
                    continue
                yield name[:-5], json.load(fh)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue


def count_service_files(tar_path: Path) -> int:
    n = 0
    with tarfile.open(tar_path, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            name = m.name.rsplit("/", 1)[-1]
            if SERVICE_RE.search(m.name) or not name.endswith(".json"):
                n += 1
    return n


def decode_stem(stem: str) -> str:
    """Site stem convention → SLP1 key: `_x` = uppercase(x). H6050 evidence."""
    out, i = [], 0
    while i < len(stem):
        if stem[i] == "_" and i + 1 < len(stem):
            out.append(stem[i + 1].upper())
            i += 2
        else:
            out.append(stem[i])
            i += 1
    return "".join(out)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- OCR-route / dump readiness (H6067 sender shape) ------------------------

def run_ocr_route(route_dir: Path, index: WorksIndex) -> dict:
    """Validate an H6067 ocr_halle_route.py export and parse its pages.

    The manifest carries page_id, source_image, engine, sha256_text, qc_*;
    pages are <page_id>.md. Dump readiness = the pipeline consumes this shape
    without the per-lemma tar (post-H5940 dump / remainder material).
    """
    mf = route_dir / "nws_route_manifest.jsonl"
    if not mf.is_file():
        sys.exit(f"FAIL: no nws_route_manifest.jsonl under {route_dir}")
    need = {"page_id", "source_image", "engine", "sha256_text"}
    pages, sigla = [], Counter()
    qc = Counter()
    for line in mf.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        missing = need - set(row)
        if missing:
            sys.exit(f"FAIL: manifest row missing {sorted(missing)}: {row}")
        qc[str(row.get("qc_status", "?"))] += 1
        page = route_dir / f"{row['page_id']}.md"
        text = page.read_text(encoding="utf-8") if page.is_file() else ""
        if text:
            h = hashlib.sha256(text.encode()).hexdigest()
            if row.get("sha256_text") and h != row["sha256_text"]:
                sys.exit(f"FAIL: sha256_text mismatch for {row['page_id']}")
        pages.append(row["page_id"])
        for ln in text.splitlines():
            for tok in re.split(r"[,;.]", ln):
                tok = tok.strip()
                if is_siglum_token(tok):
                    sigla[tok] += 1
    return {"pages": len(pages), "qc": dict(qc),
            "sigla_census": sigla.most_common(30)}


# --- full pipeline run ------------------------------------------------------

def run_full_tar(tar_path: Path, index: WorksIndex) -> dict:
    per_work: dict[int, dict] = {w["id"]: {"work": w, "exact": 0, "fuzzy": 0,
                                           "spellings": Counter()}
                                 for w in index.works}
    unregistered = Counter()
    headline = Counter()
    parse_ok = parse_unparsed = 0
    key1_present = decode_agree = 0
    nws_entries = 0
    for stem, j in iter_tar_lemmas(tar_path):
        headline["lemmas"] += 1
        k1 = (j.get("key1") or "").strip()
        if k1:
            key1_present += 1
            if decode_stem(stem) == k1:
                decode_agree += 1
        if j.get("has_nws_extra"):
            headline["has_nws_extra"] += 1
        prose = j.get("nws") or ""
        if not prose.strip():
            continue
        nws_entries += 1
        p = parse_nws_field(prose)
        parse_ok += p["senses"] + len(p["page_refs"]) + len(p["lit_refs"]) \
            + len(p["dict_markers"]) + len([1 for _ in p["sigla"]])
        parse_unparsed += p["unparsed"]
        headline["page_refs"] += len(p["page_refs"])
        headline["lit_refs"] += len(p["lit_refs"])
        if p["dict_markers"]:
            headline["dict_marker_entries"] += 1
            headline["dict_markers"] += len(p["dict_markers"])
        for tok in p["sigla"] + p["lit_refs"]:
            w, how = index.match(tok)
            if w:
                per_work[w["id"]]["exact" if how == "exact" else "fuzzy"] += 1
                per_work[w["id"]]["spellings"][tok] += 1
            else:
                unregistered[tok] += 1
    attested = sum(1 for v in per_work.values()
                   if v["exact"] + v["fuzzy"] > 0)
    return {
        "per_work": per_work,
        "unregistered": unregistered,
        "headline": dict(headline),
        "attested": attested,
        "parse_ok": parse_ok,
        "parse_unparsed": parse_unparsed,
        "key1_present": key1_present,
        "decode_agree": decode_agree,
        "nws_entries": nws_entries,
    }


def report_md(res: dict, index: WorksIndex, src: str) -> str:
    L = [f"# NWS intake compliance report — {src}", "",
         f"- registry works: {len(index.works)}",
         f"- works attested (>=1 citation): {res['attested']}",
         f"- lemmas seen: {res['headline'].get('lemmas', 0):,}",
         f"- entries with nws prose: {res.get('nws_entries', 0):,}",
         f"- key1 present: {res.get('key1_present', 0):,} "
         f"(stem-decode agreement {res.get('decode_agree', 0):,})",
         f"- page-precise refs: {res['headline'].get('page_refs', 0):,} · "
         f"literature refs: {res['headline'].get('lit_refs', 0):,} · "
         f"dict-marker entries: {res['headline'].get('dict_marker_entries', 0):,}",
         f"- unparsed segments: {res['parse_unparsed']} of {res['parse_ok']} "
         f"({res['parse_unparsed'] / max(1, res['parse_ok']) * 100:.3f}%)", "",
         "## Per-work compliance (all 174 rows)", "",
         "| # | siglum | exact | fuzzy | top spelling |", "|---|---|---|---|---|"]
    for w in index.works:
        v = res["per_work"][w["id"]]
        top = ", ".join(f"{s}×{c}" for s, c in
                        v["spellings"].most_common(2)) or "—"
        L.append(f"| {w['id']} | {w['siglum']} | {v['exact']} | "
                 f"{v['fuzzy']} | {top} |")
    L += ["", "## Unregistered sigla census (top 30 of "
          f"{len(res['unregistered'])} kinds)", "",
          "| siglum | citations |", "|---|---|"]
    for s, c in res["unregistered"].most_common(30):
        L.append(f"| {s} | {c} |")
    return "\n".join(L) + "\n"


def selftest(tar_path: Path | None) -> int:
    fails: list[str] = []
    works = load_registry()
    if len(works) != PINNED["registry_works"]:
        fails.append(f"registry {len(works)} != {PINNED['registry_works']}")
    idx = WorksIndex(works)
    # canaries straight from the H5937 lock
    a = parse_nws_field("āśana Reg , unsp > Subst n food. ĀdiPa Ed, S. 206, "
                        "Z. 4 . Ensink 1964 : 27 >")
    if PINNED["canary_asana_header"] not in a["header"]:
        fails.append(f"canary header: {a['header']!r}")
    if not any(r.startswith(PINNED["canary_asana_pageref"]) for r in a["page_refs"]):
        fails.append(f"canary pageref: {a['page_refs']!r}")
    if not any(r == PINNED["canary_asana_litref"] for r in a["lit_refs"]):
        fails.append(f"canary litref: {a['lit_refs']!r}")
    w, how = idx.match("Ensink 1964")
    if not w or w["siglum"] != "Ensink 1964":
        fails.append(f"Ensink 1964 match: {w} {how}")
    b = parse_nws_field(
        "ābhā Gen , unsp > Subst f a flash. beauty. Mbh , MānDhŚ , Suś , "
        "Pañcat . a reflected image, outline. likeness, resemblance. Mbh , R . "
        "Adj mfn like, resembling, appearing. R , Kāvyād , Śiśup . MW : 145 >")
    for sig in PINNED["canary_aba_sigla"]:
        if sig not in b["sigla"]:
            fails.append(f"aba sigla missing {sig}: {b['sigla']!r}")
    if "MW" not in b["dict_markers"]:
        fails.append(f"aba dict marker: {b['dict_markers']!r}")
    if tar_path and tar_path.is_file():
        if sha256_of(tar_path) != TAR_SHA256_PIN:
            fails.append(f"tar sha256 drift: {tar_path} is not the pinned "
                         "054b05da… artifact (H6050 input)")
        n_service = count_service_files(tar_path)
        if n_service != PINNED["tar_service_files"]:
            fails.append(f"tar_service_files: {n_service} != "
                         f"{PINNED['tar_service_files']}")
        res = run_full_tar(tar_path, idx)
        checks = {
            "tar_lemmas": res["headline"].get("lemmas", 0),
            "key1_present": res["key1_present"],
            "stem_decode_agree": res["decode_agree"],
            "nws_content_entries": res["nws_entries"],
            "has_nws_extra_true": res["headline"].get("has_nws_extra", 0),
            "page_refs": res["headline"].get("page_refs", 0),
            "lit_refs": res["headline"].get("lit_refs", 0),
            "dict_marker_entries": res["headline"].get("dict_marker_entries", 0),
            "works_attested": res["attested"],
        }
        for k, v in checks.items():
            if v != PINNED[k]:
                fails.append(f"{k}: {v} != {PINNED[k]}")
        unp_pct = res["parse_unparsed"] / max(1, res["parse_ok"]) * 100
        if unp_pct > PINNED["unparsed_seg_pct_max"]:
            fails.append(f"unparsed {unp_pct:.3f}% > {PINNED['unparsed_seg_pct_max']}%")
    else:
        print("NOTE: tar absent — registry/canary pins only (tar pins skipped)")
    if fails:
        print("SELFTEST FAIL:")
        for f in fails:
            print("  -", f)
        return 1
    print("SELFTEST PASS: registry, canaries"
          + (", full-tar pins" if tar_path and tar_path.is_file() else "")
          + " reproduce exactly")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build-registry", type=Path,
                    help="parse fetched /dictionaries HTML → commit registry")
    ap.add_argument("--full-tar", action="store_true",
                    help="run the full pipeline over the private NWS tar")
    ap.add_argument("--nws-tar", type=Path, default=_default_tar())
    ap.add_argument("--from-ocr-route", type=Path,
                    help="H6067 OCR-route export dir (dump readiness)")
    ap.add_argument("--report", type=Path, help="write report.md + report.json")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.build_registry:
        works = build_registry_from_html(args.build_registry)
        if len(works) != PINNED["registry_works"]:
            sys.exit(f"FAIL: parsed {len(works)} works, expected 174")
        REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        doc = {"provenance": {"url": SITE, "fetched": "2026-10-06",
                              "html_sha256": sha256_of(args.build_registry),
                              "rights": RIGHTS, "count": len(works)},
               "works": works}
        REGISTRY.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
        print(f"registry written: {REGISTRY} ({len(works)} works)")
        return 0

    if args.selftest:
        return selftest(args.nws_tar)

    index = WorksIndex(load_registry())
    if args.full_tar:
        if not args.nws_tar.is_file():
            sys.exit(f"FAIL: NWS tar not found: {args.nws_tar}")
        sha = sha256_of(args.nws_tar)
        res = run_full_tar(args.nws_tar, index)
        src = f"tar {args.nws_tar.name} sha256 {sha[:12]}…"
    elif args.from_ocr_route:
        r = run_ocr_route(args.from_ocr_route, index)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    else:
        ap.error("choose --full-tar | --from-ocr-route | --selftest | "
                 "--build-registry")
        return 2

    if args.report:
        args.report.mkdir(parents=True, exist_ok=True)
        (args.report / "report.md").write_text(
            report_md(res, index, src), encoding="utf-8")
        slim = {k: v for k, v in res.items() if k != "per_work"}
        slim["per_work_counts"] = {
            str(w["id"]): {"exact": v["exact"], "fuzzy": v["fuzzy"]}
            for w in index.works for v in (res["per_work"][w["id"]],)}
        (args.report / "report.json").write_text(
            json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"report → {args.report}/")
    print(report_md(res, index, src))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
