"""Cross-dictionary sense alignment — PWG ↔ MW ↔ Apte ↔ ŚKDR ↔ VCP
(H3744 wave-2 slice 1; the Sa→Sa columns are H3862, slice 2).

STAGING ONLY. Nothing here changes a public page: the render organ fires only
when `ux={"sense_align": True}`, which only `build_word_pages.py --ux-staging`
sets. (Plain `ux` truthiness would NOT do — the H3457 organs were published on
26-08-2026, so every live /w/ page is rendered with `ux` on.) Marker:
docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md.

Why a module and not just a build script: the alignment logic is the design
deliverable of this wave and has to be testable without `kosha.db` (which is
gitignored and absent in CI). Everything here is a pure function of plain
dicts; `scripts/build_sense_alignment.py` supplies the DB rows.

THE PROBLEM
-----------
The three dictionaries do not share a sense granularity and do not share a
metalanguage. PWG glosses in German, MW and Apte in English, so lexical gloss
overlap — the obvious signal — is structurally unavailable across the PWG
boundary, which is exactly the boundary the wave exists to cross.

THE BRIDGE: SHARED LITERARY WITNESS
-----------------------------------
Both traditions cite their sources per sense, in `<ls>`. The canonical case:

    PWG  nAgadanta 1〉a〉  "Elephantenzahn, Elfenbein"   <ls>MBH. 12,3630</ls>
    MW   L104994          "elephant's tusk or ivory"    <ls>MBh.</ls>
    PWG  nAgadanta 1〉b〉  "Pflock in der Wand …"        <ls>PAÑCAT. 116,19</ls>
    MW   L104995          "a peg in the wall …"         <ls>Pañc.</ls>; <ls>Kathās.</ls>

The tusk↔Pflock split — the whole point of the नागदन्त thread — is recoverable
from the citations alone, in any pair of languages. Two senses that cite the
same text are candidates for being the same meaning.

A shared citation is only *evidence*, and its strength is not constant: two
senses both citing `MBh.` say almost nothing when every sense of the lemma
cites `MBh.`, and say a great deal when nothing else does. So every witness is
weighted by its inverse document frequency **within the lemma** — `1/df`, df =
how many senses of this lemma (across all three dictionaries) cite it. A
witness shared by exactly one sense on each side scores 0.5; a witness common
to six senses scores 0.167 and cannot carry an edge alone.

THE SECOND BRIDGE (H3862): PRINTED ATTRIBUTION
----------------------------------------------
The Sa→Sa kośas carry **no `<ls>` at all** — measured, not assumed: 0 of 42,531
ŚKDR records and 0 of 50,135 VCP records contain one. They mark attribution in
running Sanskrit prose (`ityamaraḥ`, `iti medinī`, `yathā suśrute`), so the
weighted-witness bridge above does not exist for them by construction, and the
gloss bridge is barred by the language fence (their metalanguage is Sanskrit).

What does exist is the reverse direction, and it is printed rather than
inferred: **PWG cites ŚKDR and Medinī in its own `<ls>`** — 1,227 and 1,824
times across the 500-headword pilot, touching 479 of its 500 lemmas. A PWG
sense whose `<ls>` names ŚKDR is *saying* that this meaning is the one
Śabdakalpadruma records for the lemma. When ŚKDR has an entry for that lemma,
that is an alignment edge asserted by a dictionary, not derived by us.

It takes exactly the same weighting as `ls`, from exactly the same `df` table:
`ŚKDR.` is already a witness key, so its 1/df within the lemma is already
computed. A lemma where one PWG sense of fifteen cites ŚKDR scores 1.0 and the
edge is sharp; a lemma where nine senses do scores 0.111 and cannot carry an
edge at all. **No new constant is introduced by this channel** — τ decides it.

An open-vocabulary reading of the kośas' own `iti X` prose was tried first and
rejected: it re-invented witnesses through a side door PREFIX_MIN closes. On
the pilot it matched PWG's `PRAT.` to `pratyarthin` ("counter-claimant") and
`BUDDH.` to `buddhim`, because the attribution particle is followed by an
ordinary word far more often than by a source name. Measured yield was 73 of
707 records, most of them false. The dead end is recorded in the build report;
a closed, curated source vocabulary would be the honest version of it, and it
is not this slice.

METHODS (each edge records which one carried it)
------------------------------------------------
`ls`      shared weighted literary witness. The only method that crosses the
          German/English boundary. Score = Σ 1/df over shared witnesses, ≤ 1.
`gloss`   Jaccard over content tokens. Usable ONLY between two dictionaries
          that gloss in the SAME language, and only when that language is
          English (MW↔Apte) — never across PWG (German) and never across
          ŚKDR/VCP (Sanskrit), where it would silently measure nothing.
`attrib`  a western sense's `<ls>` names the Sa→Sa kośa itself, and that kośa
          has an entry for the lemma. Weighted 1/df like `ls`, off the same
          table. Directional evidence: the two sides do not converge
          independently, one of them points at the other.
`ls+gloss` both fired; score is the max, and the pair is the most trustworthy
          class in the table.

GROUPING: BEST MATCH, NOT REACHABILITY
--------------------------------------
Edges at or above `TAU` are candidates. They are then resolved by a greedy best
matching **per dictionary pair**: every sense takes at most one partner in each
other dictionary — its highest-scoring one — and a losing candidate is recorded
as `outranked` rather than absorbed.

Transitive closure was tried first and is wrong here. `amṛta`'s MW and Apte
senses all cite RV/MBh and all share wording, so one component swallowed *not
dead*, *nectar* and *N. pr. the mother of Parikṣit* and presented them as one
meaning: a false claim wearing the shape of a row. "These two are each other's
strongest evidence match" is a claim the table can defend; "a path exists
between them" is not.

Groups are the components over the MATCHED edges. A group touching ≥2
dictionaries is `aligned`; a lone sense is `unaligned` and carries a failure
class.

FAILURE CLASSES — recorded, never hidden
----------------------------------------
`absent-dictionary`   the lemma has no entry at all in one of the three.
`cross-language-gap`  a PWG sense with no `<ls>` whatsoever: the bridge does
                      not exist for it by construction, and gloss overlap
                      cannot cross German→English. Structurally unalignable
                      by this method, not a tuning failure.
`no-shared-witness`   the sense cites sources, but none of them is cited by any
                      cross-dictionary sense of the lemma.
`witness-too-common`  the only shared witnesses fall below TAU on weight — the
                      citation is real but has no discriminating power.
`outranked`           the sense had a qualifying partner, but that partner had a
                      better match. Each sense takes at most one partner per other
                      dictionary, so a losing candidate is recorded rather than
                      folded into somebody else's row.
`no-gloss`            a structural chunk (PWG `<div>` carrying only `<lex>m.</lex>`)
                      with no gloss text; excluded before alignment, counted.
`no-citation-apparatus`
                      a ŚKDR/VCP sense that no western sense attributes to it:
                      it has no `<ls>` of its own (the kośas have none at all),
                      and its gloss is Sanskrit, so both bridges are closed for
                      it. The Sa→Sa counterpart of `cross-language-gap` — a
                      property of the source format, not a tuning failure.
On the group side, `granularity-many-to-many` marks a component in which two or
more senses of one dictionary land in the same meaning as two or more of
another — a real alignment, at a coarser grain than either dictionary's own.

WHAT THIS IS NOT
----------------
Not word-sense disambiguation, not a re-ordering of anybody's senses, not a
claim that a group is a lexicographic unit. It is a sidecar assertion that
these senses are *witnessed by the same texts*, with the weight of that
evidence printed next to it.
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

# --- marked defaults (H3744). Every one of these is logged into the build report.
TAU = 0.30              # edge survival threshold
GLOSS_FLOOR = 0.20      # Jaccard floor below which a gloss edge is not drawn
PREFIX_MIN = 4          # min chars for abbreviation prefix-folding (see fold_witnesses)
MAX_GLOSS = 260         # gloss truncation for the table / viewer

# The gloss channel is fenced BY DECLARED LANGUAGE, not by an implicit tuple.
# Three metalanguages are now in the table and Jaccard is meaningful inside
# exactly one of them: two dictionaries may be compared on wording only when
# they gloss in the same language AND that language is English (the case where
# Apte often reprints MW's own wording, which is what makes the signal strong).
# German↔English measured nothing in slice 1; Sanskrit↔Sanskrit would measure
# even less, since ŚKDR and VCP share a scholastic idiom in which two unrelated
# senses routinely repeat `ityamaraḥ`, `ityarthaḥ`, `iti purāṇam`.
GLOSS_LANG = {"pwg": "de", "mw": "en", "ap90": "en", "skd": "sa", "vcp": "sa"}
GLOSS_CHANNEL_LANG = "en"
ENGLISH_DICTS = tuple(d for d, lg in GLOSS_LANG.items() if lg == GLOSS_CHANNEL_LANG)

SASA_DICTS = ("skd", "vcp")      # Sanskrit-to-Sanskrit kośas (H3862)
DICTS = ("pwg", "mw", "ap90", "skd", "vcp")

# The abbreviation table for the `attrib` channel: which witness keys, as the
# WESTERN dictionaries spell them in `<ls>`, name each Sa→Sa kośa. Written out
# rather than prefix-matched on purpose — `PREFIX_MIN` stays at 4 and is not
# weakened to reach these, because a table is auditable and a shorter prefix
# floor would let `R.` fold onto `RV.` everywhere else in the build.
#
# Keys are post-`witness_key` normalisations: `ŚKDR.` → `skdr`, `Śabdak.` →
# `sabdak`, `VĀCASPATYA` → `vacaspatya`. Medinī's `MED.` is deliberately absent
# — see the `attrib` note in the build report: Medinī is not in CDSL at all, so
# there is no column for `MED.` to point at.
ATTRIB_KEYS = {
    "skd": ("skdr", "sabdak", "sabdakalpadr"),
    "vcp": ("vcp", "vacaspatya", "vacasp"),
}

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_LS = re.compile(r"<ls\b([^>]*)>(.*?)</ls>", re.S)
_LS_N = re.compile(r'\bn\s*=\s*"([^"]*)"')
_NONALPHA = re.compile(r"[^a-z.]")
_DOTS = re.compile(r"\.{2,}")

# Tokens that carry no sense information in a dictionary gloss.
_STOP = {
    "the", "a", "an", "of", "or", "and", "to", "in", "on", "for", "with", "as",
    "is", "are", "be", "being", "any", "one", "esp", "cf", "also", "not", "by",
    "at", "from", "that", "this", "it", "its", "his", "her", "their", "who",
    "which", "name", "n", "m", "f", "mfn", "ind", "adj", "ved", "l", "w", "r",
    "sometimes", "often", "used", "said", "kind", "sort", "etc", "see", "pl",
}


def strip_markup(s: str, limit: int = MAX_GLOSS) -> str:
    t = _WS.sub(" ", _TAG.sub(" ", s or "")).strip()
    if limit and len(t) > limit:
        t = t[: limit - 1] + "…"
    return t


_LS_SPAN = re.compile(r"<ls\b[^>]*>.*?</ls>", re.S)
_S_SPAN = re.compile(r"<s\b[^>]*>.*?</s>", re.S)
_S_SPAN_TEXT = re.compile(r"<s\b[^>]*>(.*?)</s>", re.S)
_I_SPAN = re.compile(r"<i\b[^>]*>(.*?)</i>", re.S)
_LEAD_MARK = re.compile(r"^[\s—\-–·]*(?:[0-9a-zA-Z]?[〉\)]\s*)*")


def sense_gloss(raw_body: str, dct: str, limit: int = MAX_GLOSS) -> str:
    """The DEFINITION of a sense, not its apparatus.

    A raw Cologne sense span is definition + citations + quoted Sanskrit, and
    the last two are far the bulkiest. `<ls>` (literary source) and `<s>`
    (Sanskrit in SLP1) are stripped for display: they are the evidence, already
    surfaced as weighted witnesses, and a page cell full of `de\\veBya\\H
    kama^vfRlta` is not a gloss.

    PWG marks its German definition with `<i>`, so when a PWG span has any `<i>`
    the definition is exactly those runs and nothing else. MW and Apte have no
    such marker, so they fall back to the stripped remainder.

    ŚKDR and VCP invert the rule (H3862): their record is `<s>` end to end,
    because their metalanguage IS Sanskrit. Stripping `<s>` there would leave an
    empty string and the sense would be discarded as a structural chunk, so for
    them the `<s>` runs are kept — they are the definition, not the apparatus.
    The text comes back in SLP1, as it is stored; transliteration for display is
    the caller's business (`scripts/build_sense_alignment.py` renders IAST).
    """
    if dct in SASA_DICTS:
        runs = [strip_markup(x, 0) for x in _S_SPAN_TEXT.findall(raw_body or "")]
        t = " ".join(r for r in runs if r).strip()
        if not t:
            t = strip_markup(raw_body or "", 0)
        t = _WS.sub(" ", t).strip(" .,;:")
        return t[: limit - 1] + "…" if limit and len(t) > limit else t
    body = _LS_SPAN.sub(" ", raw_body or "")
    body = _S_SPAN.sub(" ", body)
    if dct == "pwg":
        runs = [strip_markup(x, 0) for x in _I_SPAN.findall(body)]
        runs = [r for r in runs if r]
        if runs:
            t = "; ".join(runs)
            return t[: limit - 1] + "…" if limit and len(t) > limit else t
    t = _LEAD_MARK.sub("", strip_markup(body, 0)).strip(" .,;:")
    return t[: limit - 1] + "…" if limit and len(t) > limit else t


def deaccent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def witness_key(raw: str) -> str:
    """Normalise one `<ls>` source citation to a comparable key.

    PWG cites in upper-case German style (`MBH. 12,3630`, `PAÑCAT. 116,19`,
    `H. an. 4,111`); MW/Apte in mixed case (`MBh.`, `Pañc.`, `Kathās.`). Drop
    everything from the first digit (the locus, which the two traditions
    address differently), deaccent, lower-case, keep letters and dots.

        'MBH. 12,3630'  -> 'mbh'      'MBh.'   -> 'mbh'
        'PAÑCAT. 116,19'-> 'pancat'   'Pañc.'  -> 'panc'
        'H. an. 4,111'  -> 'h.an'     'Kathās.'-> 'kathas'

    `pancat`/`panc` differ; `fold_witnesses` folds a longer key onto a shorter
    one it extends. Returns '' for a citation with no alphabetic head.
    """
    t = raw or ""
    m = re.search(r"\d", t)
    if m:
        t = t[: m.start()]
    t = _NONALPHA.sub("", deaccent(t).lower())
    t = _DOTS.sub(".", t).strip(".")
    return t


def extract_ls(raw_body: str) -> list[str]:
    """Every `<ls>` source key in a sense span, including the `n="…"` form
    (`<ls n="SUŚR.">2,62,6</ls>` — continuation citations whose source lives in
    the attribute, not the text)."""
    out: list[str] = []
    for attrs, text in _LS.findall(raw_body or ""):
        n = _LS_N.search(attrs)
        k = witness_key(n.group(1)) if n else witness_key(_TAG.sub(" ", text))
        if k:
            out.append(k)
    return out


def fold_witnesses(keys) -> dict[str, str]:
    """Map every witness key of one lemma onto a cluster representative.

    A longer key that *extends* a shorter one (`pancat` ⊃ `panc`) is the same
    text abbreviated at two lengths, so it folds onto the shorter. Folding is
    restricted to keys of at least `PREFIX_MIN` characters: at two characters
    `r` (Rāmāyaṇa) is a prefix of `rv` (Ṛgveda) and folding them would invent a
    witness that does not exist.
    """
    uniq = sorted(set(k for k in keys if k), key=lambda k: (len(k), k))
    rep: dict[str, str] = {}
    for k in uniq:
        r = k
        for short in uniq:
            if short == k:
                break
            if len(short) >= PREFIX_MIN and k.startswith(short):
                r = rep.get(short, short)
                break
        rep[k] = r
    return rep


def gloss_tokens(gloss: str) -> set[str]:
    toks = re.findall(r"[a-z]{3,}", deaccent(gloss or "").lower())
    return {t for t in toks if t not in _STOP}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def gloss_channel_open(d1: str, d2: str) -> bool:
    """May wording be compared between these two dictionaries at all?

    Only inside one metalanguage, and only when that metalanguage is English.
    This is the fence slice 1 drew across German and slice 2 has to draw again
    across Sanskrit: a Jaccard between a German and an English gloss, or between
    two Sanskrit ones, does not measure a weak signal — it measures nothing, and
    returns a number anyway. Relaxing it quietly is the failure mode this
    function exists to make impossible to reach by accident.
    """
    lang = GLOSS_LANG.get(d1)
    return lang is not None and lang == GLOSS_LANG.get(d2) == GLOSS_CHANNEL_LANG


def attrib_witnesses(s_west: dict, s_sasa: dict) -> list[str]:
    """The keys by which `s_west` names `s_sasa`'s kośa in its own `<ls>`.

    Empty unless exactly one side is a Sa→Sa kośa and the other cites it. See
    the module docstring: this is a printed attribution, not an inference.
    """
    if s_sasa["dict"] not in SASA_DICTS or s_west["dict"] in SASA_DICTS:
        return []
    wanted = set(ATTRIB_KEYS.get(s_sasa["dict"], ()))
    return sorted(set(s_west["ls"]) & wanted)


def score_pair(s1: dict, s2: dict, df: dict[str, int]) -> tuple[float, str, list[str]]:
    """(score, method, shared witnesses) for two senses of the same lemma from
    two different dictionaries. `df` is the per-lemma document frequency of each
    folded witness cluster."""
    shared = sorted(set(s1["ls"]) & set(s2["ls"]))
    ls_score = 0.0
    for w in shared:
        d = df.get(w, 2)
        ls_score += 1.0 / d if d else 0.0
    ls_score = min(ls_score, 1.0)

    g_score = 0.0
    if gloss_channel_open(s1["dict"], s2["dict"]):
        g_score = jaccard(s1["toks"], s2["toks"])
        if g_score < GLOSS_FLOOR:
            g_score = 0.0

    # `attrib` (H3862) — same 1/df weighting, same `df` table, no new constant.
    a_keys = attrib_witnesses(s1, s2) or attrib_witnesses(s2, s1)
    a_score = 0.0
    for w in a_keys:
        d = df.get(w, 2)
        a_score += 1.0 / d if d else 0.0
    a_score = min(a_score, 1.0)

    if ls_score and g_score:
        method = "ls+gloss"
    elif ls_score:
        method = "ls"
    elif g_score:
        method = "gloss"
    elif a_score:
        method = "attrib"
    else:
        method = ""
    # `attrib` never outranks a shared-witness edge: it is one dictionary
    # pointing at another, not two of them converging on a third text.
    if method == "attrib":
        return a_score, method, a_keys
    return max(ls_score, g_score), method, shared


def _components(n: int, edges) -> list[list[int]]:
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j in edges:
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    return [sorted(v) for _k, v in sorted(groups.items())]


def align_lemma(senses: list[dict], present_dicts=None, tau: float = TAU) -> dict:
    """Align one lemma's senses.

    `senses`: [{dict, sense_id, label, gloss, ls:[key,…]}] — ONE lemma, any mix
    of the three dictionaries. `present_dicts`: which of the three have an entry
    for this lemma at all (used to tell `absent-dictionary` from a real miss);
    defaults to the dictionaries seen in `senses`.

    Returns {groups, edges, senses, dropped, stats}. Never mutates the input
    beyond adding derived keys to copies.
    """
    present = set(present_dicts if present_dicts is not None
                  else (s["dict"] for s in senses))
    live, dropped = [], []
    for s in senses:
        g = strip_markup(s.get("gloss", ""))
        rec = dict(s, gloss=g, ls=list(s.get("ls") or []))
        if len(re.sub(r"[^A-Za-zÀ-ɏ]", "", g)) < 3:
            rec["failure_class"] = "no-gloss"
            dropped.append(rec)
            continue
        live.append(rec)

    rep = fold_witnesses([w for s in live for w in s["ls"]])
    for s in live:
        s["ls"] = sorted({rep.get(w, w) for w in s["ls"]})
        s["toks"] = gloss_tokens(s["gloss"])
    df: dict[str, int] = defaultdict(int)
    for s in live:
        for w in s["ls"]:
            df[w] += 1

    candidates, near_miss = defaultdict(list), defaultdict(list)
    for i in range(len(live)):
        for j in range(i + 1, len(live)):
            if live[i]["dict"] == live[j]["dict"]:
                continue
            sc, method, shared = score_pair(live[i], live[j], df)
            if sc >= tau and method:
                pair = tuple(sorted((live[i]["dict"], live[j]["dict"])))
                candidates[pair].append({"i": i, "j": j, "score": round(sc, 3),
                                         "method": method, "witnesses": shared})
            elif shared:
                near_miss[i].append(sc)
                near_miss[j].append(sc)

    # GREEDY BEST MATCHING per dictionary pair, not transitive closure.
    #
    # Closure over "there is a path" produced blobs: `amṛta`'s MW and Apte senses
    # all cite RV/MBh and all overlap lexically, so one component swallowed
    # "not dead", "nectar" and "N. pr. the mother of Parikṣit" and called them one
    # meaning. That is a false claim dressed as a row. Matching each sense to at
    # most ONE partner per other dictionary — its best-scoring one — makes the row
    # say something defensible: these two are each other's strongest evidence
    # match, not merely reachable from each other.
    edges, outranked = [], set()
    for pair in sorted(candidates):
        taken: set[int] = set()
        for e in sorted(candidates[pair], key=lambda e: (-e["score"], e["i"], e["j"])):
            if e["i"] in taken or e["j"] in taken:
                outranked.add(e["i"])
                outranked.add(e["j"])
                continue
            taken.add(e["i"])
            taken.add(e["j"])
            edges.append(e)
    matched = {e["i"] for e in edges} | {e["j"] for e in edges}
    outranked -= matched

    comps = _components(len(live), [(e["i"], e["j"]) for e in edges])
    edge_by_comp = defaultdict(list)
    idx_comp = {}
    for ci, comp in enumerate(comps):
        for i in comp:
            idx_comp[i] = ci
    for e in edges:
        edge_by_comp[idx_comp[e["i"]]].append(e)

    groups = []
    for ci, comp in enumerate(comps):
        members = [live[i] for i in comp]
        by_dict = defaultdict(list)
        for m in members:
            by_dict[m["dict"]].append(m)
        ge = edge_by_comp[ci]
        n_dicts = len(by_dict)
        aligned = n_dicts >= 2
        flags = []
        if aligned and sum(1 for d in by_dict.values() if len(d) >= 2) >= 2:
            flags.append("granularity-many-to-many")
        failure = ""
        if not aligned:
            m = members[0]
            # Precedence is deliberate: a class only fires when the ones above it
            # cannot explain the miss. `absent-dictionary` is the strongest claim
            # (there was nothing to align against at all) and so is tested first;
            # it must NOT absorb a lemma where a second dictionary is present and
            # simply disagrees.
            if len(present) < 2:
                failure = "absent-dictionary"
            elif comp[0] in outranked:
                failure = "outranked"
            elif near_miss.get(comp[0]):
                failure = "witness-too-common"
            elif m["dict"] in SASA_DICTS:
                # ŚKDR/VCP never have `<ls>` — the format has none — and their
                # gloss is Sanskrit, so both bridges are shut. The only one that
                # could have opened is a western sense attributing this lemma to
                # the kośa, and none did.
                failure = "no-citation-apparatus"
            elif not m["ls"]:
                failure = ("cross-language-gap" if m["dict"] == "pwg"
                           else "no-shared-witness")
            else:
                failure = "no-shared-witness"
        # `ls+gloss` is itself an edge method, so flatten to atoms before joining —
        # otherwise a component with an `ls` edge and an `ls+gloss` edge reads `ls+ls+gloss`.
        atoms = sorted({a for e in ge for a in e["method"].split("+")})
        methods = atoms or ["singleton"]
        groups.append({
            "members": members,
            "by_dict": {d: by_dict.get(d, []) for d in DICTS},
            "edges": ge,
            "status": "aligned" if aligned else "unaligned",
            "failure_class": failure,
            "flags": flags,
            "score": round(max([e["score"] for e in ge], default=0.0), 3),
            "method": "+".join(methods) if methods != ["singleton"] else "singleton",
            "witnesses": sorted({w for e in ge for w in e["witnesses"]}),
            "shape": "-".join(str(len(by_dict.get(d, []))) for d in DICTS),
        })
    # Reading order: aligned first; among aligned, the ones spanning MORE
    # dictionaries first, then by evidence strength. Sorting on score alone would
    # bury every PWG-crossing row — the point of the wave — under MW↔Apte gloss
    # pairs, which score 1.0 whenever Apte reprints MW's wording, as it often does.
    groups.sort(key=lambda g: (g["status"] != "aligned",
                               -sum(1 for v in g["by_dict"].values() if v),
                               -g["score"], g["shape"]))
    stats = {
        "n_senses": len(live),
        "n_dropped_no_gloss": len(dropped),
        "n_groups": len(groups),
        "n_aligned": sum(1 for g in groups if g["status"] == "aligned"),
        "n_unaligned": sum(1 for g in groups if g["status"] == "unaligned"),
        "present_dicts": sorted(present),
    }
    return {"groups": groups, "senses": live, "dropped": dropped, "stats": stats}
