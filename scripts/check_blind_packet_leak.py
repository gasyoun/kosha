#!/usr/bin/env python
"""H5296 — reusable blind-packet metadata-leak gate for evaluation decks.

Turns the H5070 canary leak (kosha PR #631: the synthetic control was uniquely
identifiable from `stratum_eligible=0` + `population_share=0.000000`) into a
mechanical gate. It examines the EXACT rendered payload a reviewer receives --
the adjudication cards as printed by the family renderer -- never a pre-render
object, and asserts the planted control is not uniquely identifiable from
metadata, field presence/missingness, formatting, or ordering position. The
control's identity may live in the hidden key; it must not live in the packet.

Layers
  default   the rendered reviewer payload: field tells, dict-presence tells,
            ordering/position, formatting class, and the #631 mechanism check
            that hidden metadata (stratum/score/method/synthetic) never leaks
            into the rendered text.
  --strict-deck-metadata
            additionally runs the full TSV coded-column arithmetic (the #631
            specimen check) over the packet-of-record. Frozen decks predating
            this gate may carry residuals here (e.g. a unique canary score);
            the layer exists so builders of NEW decks can prove their TSV is
            clean too. Findings are reported, never silently suppressed.

Usage (exit 0 clean / 2 leak / 1 gate defect):
  python scripts/check_blind_packet_leak.py \
      --deck data/concordance/selective_risk_skd/review_deck.tsv \
      --key  data/concordance/selective_risk_skd/canary_key.json

  # RED proof: plant a leak in a temp copy, expect the gate to catch it.
  # The original packet is never modified; exit 0 when caught, 1 when not.
  python scripts/check_blind_packet_leak.py --deck D --key K --mutate unique_metadata
"""
from __future__ import annotations

import argparse, csv, hashlib, json, re, subprocess, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def majority_pattern(ids: list[str]) -> str | None:
    """Format pattern shared by most rendered card ids, e.g. r'C\\d{3}'."""
    best, best_n = None, 0
    for pid in ids:
        pat = re.sub(r"\d", r"\\d", re.escape(pid))
        n = sum(1 for other in ids if re.fullmatch(pat, other))
        if n > best_n:
            best, best_n = pat, n
    return best

ROW_INTRINSIC = ("card", "group_id", "lemma_slp1")  # uniqueness is sampling variance
HIDDEN_LABELS = ("stratum", "score=", "method=", "synthetic", "population_share",
                 "stratum_eligible")
MUTATIONS = ("unique_metadata", "ordering", "missing_gloss", "formatting",
             "legacy_hidden_metadata")
EXIT_CLEAN, EXIT_GATE_DEFECT, EXIT_LEAK = 0, 1, 2


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_deck(path: Path):
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        return reader.fieldnames or [], list(reader)


def control_card_id(deck: Path, key: dict) -> str | None:
    """Map the hidden group_id to the packet card id (key knowledge only)."""
    _, rows = load_deck(deck)
    hits = [r["card"] for r in rows if r.get("group_id") == key["canary_group_id"]]
    return hits[0] if len(hits) == 1 else None


# ---------------------------------------------------------------- rendered layer

def render_deck(deck: Path, renderer: Path) -> list[dict]:
    """Run the family renderer; parse the exact card text a reviewer sees."""
    out = subprocess.run(
        [sys.executable, str(renderer), "--deck", str(deck), "--width", "400"],
        capture_output=True, text=True, encoding="utf-8", check=True).stdout
    cards, cur = [], None
    for line in out.splitlines():
        if line.startswith("=" * 8):
            if cur:
                cards.append(cur)
            cur = {"lines": [], "header": {}}
            continue
        if cur is None:
            continue
        cur["lines"].append(line)
        if line.startswith("C") and "lemma=" in line and "header" in cur and not cur["header"]:
            parts = {}
            for token in line.split("  "):
                token = token.strip()
                if token.startswith("C") and token[1:].isdigit():
                    parts["card"] = token
                elif "=" in token:
                    k, v = token.split("=", 1)
                    parts[k.strip()] = v.strip()
            cur["header"] = parts
        elif line.startswith("  ") and line.strip():
            cur.setdefault("dicts", []).append(line.strip().split(None, 1)[0].split("(")[0])
    if cur:
        cards.append(cur)
    return cards


def check_rendered(cards: list[dict], control_id: str) -> list[dict]:
    """Findings from the rendered text alone; empty list = clean packet."""
    findings = []
    others = [c for c in cards if c["header"].get("card") != control_id]
    ctrl = next((c for c in cards if c["header"].get("card") == control_id), None)
    if ctrl is None:
        return [{"check": "rendered_control_presence",
                 "detail": f"control card {control_id} missing from rendered output"}]
    ctrl_sig = tuple(sorted(ctrl.get("dicts", [])))
    other_sigs = {tuple(sorted(c.get("dicts", []))) for c in others}
    if ctrl_sig not in other_sigs:
        findings.append({"check": "rendered_missingness_tell", "detail":
                         f"control's dictionary-presence signature {list(ctrl_sig)} "
                         f"is shared by no other rendered card"})
    for field in ("shape", "witnesses"):
        value = ctrl["header"].get(field, "")
        if value not in {c["header"].get(field, "") for c in others}:
            findings.append({"check": "rendered_field_tell", "column": field,
                             "detail": f"rendered {field}={value!r} is unique to the control"})
    idx = next(i for i, c in enumerate(cards) if c is ctrl)
    if idx == 0 or idx == len(cards) - 1:
        findings.append({"check": "rendered_position_tell", "detail":
                         f"control is card {idx + 1} of {len(cards)} (first/last position)"})
    ids = [c["header"].get("card", "") for c in cards if c["header"].get("card")]
    ctrl_id = ctrl["header"].get("card", "")
    majority_fmt = majority_pattern([i for i in ids if i != ctrl_id])
    if majority_fmt and not re.fullmatch(majority_fmt, ctrl_id):
        findings.append({"check": "rendered_format_tell", "detail":
                         f"control's card id {ctrl_id!r} breaks the packet-wide id format "
                         f"{majority_fmt!r} every other card follows"})
    # formatting: the control's longest rendered line must not stand alone
    lens = [max((len(l) for l in c["lines"]), default=0) for c in cards]
    ci = next(i for i, c in enumerate(cards) if c is ctrl)
    width_bucket = lambda n: "wide" if n > 400 else "normal"
    if width_bucket(lens[ci]) not in {width_bucket(n) for i, n in enumerate(lens) if i != ci}:
        findings.append({"check": "rendered_format_tell", "detail":
                         f"control's rendered line width ({lens[ci]} chars) has a format "
                         f"class no other card uses"})
    # the #631 mechanism itself: hidden metadata must never reach the packet
    rendered_text = "\n".join(l for c in cards for l in c["lines"])
    for label in HIDDEN_LABELS:
        if label in rendered_text:
            findings.append({"check": "rendered_hidden_metadata", "detail":
                             f"hidden-metadata label {label!r} appears in the rendered packet"})
    return findings


# --------------------------------------------------------------------- TSV layer

def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _decimals(value: str) -> int | None:
    value = value.strip()
    return len(value.split(".", 1)[1]) if "." in value else None


def coded_columns(fields, id_columns):
    return [f for f in fields
            if f not in id_columns and f not in ROW_INTRINSIC
            and not f.endswith("_gloss") and not f.endswith("_sense_ids")]


def check_deck_tsv(fields, rows, key, id_columns) -> list[dict]:
    """Full #631-class arithmetic on the packet-of-record (strict layer)."""
    findings = []
    gid = key["canary_group_id"]
    hits = [r for r in rows if r.get("group_id") == gid]
    if len(hits) != 1:
        return [{"check": "control_presence",
                 "detail": f"canary row must appear exactly once, found {len(hits)}"}]
    control = hits[0]
    real = [r for r in rows if r is not control]
    coded = coded_columns(fields, id_columns)

    for col in coded:
        value = (control.get(col) or "").strip()
        peers = {(r.get(col) or "").strip() for r in real}
        if value and value not in peers:
            findings.append({"check": "field_tell", "column": col, "value": value,
                             "detail": f"control's {col}={value!r} is shared by no real row"})

    sig = tuple((control.get(c) or "").strip() != "" for c in coded)
    if not any(tuple((r.get(c) or "").strip() != "" for c in coded) == sig for r in real):
        findings.append({"check": "missingness_tell", "detail":
                         "control's empty/non-empty field signature is shared by no real row"})

    for col in coded:
        cv = (control.get(col) or "").strip()
        if not _is_number(cv):
            continue
        real_fmts = {_decimals(r[col]) for r in real
                     if (r.get(col) or "").strip() and _is_number(r[col])}
        real_fmts.discard(None)
        cf = _decimals(cv)
        if real_fmts and cf is not None and cf not in real_fmts:
            findings.append({"check": "format_tell", "column": col, "detail":
                             f"control's {col}={cv!r} has {cf} decimals, a numeric format "
                             f"no real row uses"})
    if sum(1 for r in real
           if tuple((r.get(c) or "").strip() for c in coded)
           == tuple((control.get(c) or "").strip() for c in coded)) == 0:
        findings.append({"check": "joint_tell", "detail":
                         "control's full coded-column tuple is unique in the packet"})
    return findings


# -------------------------------------------------------------------- mutations

def mutate_deck(deck: Path, key_path: Path, name: str, out: Path) -> None:
    fields, rows = load_deck(deck)
    key = json.loads(key_path.read_text(encoding="utf-8"))
    rows = [dict(r) for r in rows]
    control = next(r for r in rows if r["group_id"] == key["canary_group_id"])
    if name == "unique_metadata":        # #631-analogue on the reviewer surface
        control["shape"] = "9-9-9-9-9-9"
        control["witnesses"] = "zzz"
    elif name == "ordering":
        rows.remove(control)
        rows.append(control)
    elif name == "missing_gloss":
        control["mw_gloss"] = ""
    elif name == "formatting":
        control["card"] = control["card"].replace("C0", "C", 1) or control["card"]
    elif name == "legacy_hidden_metadata":   # the literal PR #631 specimen
        control["stratum_eligible"] = "0"
        control["population_share"] = "0.000000"
    else:
        raise SystemExit(f"unknown mutation {name}")
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


# ------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deck", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=True)
    ap.add_argument("--renderer", type=Path,
                    default=Path(__file__).resolve().parent / "render_selective_risk_deck.py")
    ap.add_argument("--id-columns", nargs="*", default=[])
    ap.add_argument("--strict-deck-metadata", action="store_true",
                    help="also run the #631-class arithmetic on the deck TSV")
    ap.add_argument("--mutate", choices=MUTATIONS, action="append", default=[],
                    help="RED proof on a temp copy; original packet untouched")
    ap.add_argument("--expect-deck-sha256", help="pin the packet hash (re-test binding)")
    args = ap.parse_args()

    deck_hash = sha256_file(args.deck)
    print(f"packet(deck) sha256  {deck_hash}")
    print(f"hidden key  sha256  {sha256_file(args.key)}")
    if args.expect_deck_sha256 and args.expect_deck_sha256 != deck_hash:
        print(f"FAIL deck sha256 != expected {args.expect_deck_sha256}")
        return EXIT_GATE_DEFECT
    key = json.loads(args.key.read_text(encoding="utf-8"))
    control_id = control_card_id(args.deck, key)
    if control_id is None:
        print("FAIL canary group_id maps to no single deck card")
        return EXIT_GATE_DEFECT

    rc = EXIT_CLEAN
    # GREEN: the rendered reviewer payload must be clean
    findings = check_rendered(render_deck(args.deck, args.renderer), control_id)
    if findings:
        print("FAIL rendered reviewer packet leaks:")
        for f in findings:
            print(f"  {f}")
        return EXIT_LEAK
    n = len(load_deck(args.deck)[1])
    print(f"GREEN  {args.deck.name}: control {control_id} not identifiable from the "
          f"rendered packet ({n} cards)")

    if args.strict_deck_metadata:
        fields, rows = load_deck(args.deck)
        strict = check_deck_tsv(fields, rows, key, set(args.id_columns) | {"card"})
        if strict:
            print(f"STRICT deck-TSV findings ({len(strict)}) — packet-of-record residuals, "
                  f"each needs a documented limitation or a builder fix:")
            for f in strict:
                print(f"  {f}")
        else:
            print("STRICT deck-TSV: clean (#631-class arithmetic found nothing)")

    # RED: every requested mutation must be caught by the layer it targets —
    # surface mutations by the rendered packet, the #631 specimen by the
    # strict TSV arithmetic — so receipts are attributable to the mutation,
    # never to a pre-existing frozen-deck residual.
    for name in args.mutate:
        with tempfile.TemporaryDirectory() as tmp:
            mutated = Path(tmp) / f"deck_mutated_{name}.tsv"
            mutate_deck(args.deck, args.key, name, mutated)
            if name == "legacy_hidden_metadata":
                fields, rows = load_deck(mutated)
                caught = check_deck_tsv(fields, rows, key, set(args.id_columns) | {"card"})
            else:
                mid = control_card_id(mutated, key)
                caught = check_rendered(render_deck(mutated, args.renderer), mid) \
                    if mid else [{"check": "rendered_control_presence",
                                  "detail": "control unresolvable after mutation"}]
            mhash = sha256_file(mutated)
        if caught:
            checks = sorted({f["check"] for f in caught})
            print(f"RED    mutation={name}: caught by {','.join(checks)} "
                  f"(mutated packet sha256 {mhash})")
        else:
            print(f"GATE DEFECT mutation={name}: the planted leak went unnoticed")
            rc = EXIT_GATE_DEFECT
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
