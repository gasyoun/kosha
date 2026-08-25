"""kosha P5 — the word page template (H537 / P5_ADVANCED_UI_DESIGN.md §3, §5).

ONE render path shared by both P5-4 targets:

  * the static prerender (scripts/build_word_pages.py) — reads a committed
    per-lemma card (docs/cards/<token>.json) and writes /w/<token>.html;
  * the FastAPI SSR route (app/main.py GET /w/{slp1}) — builds the same card
    shape from the live DB and renders it.

Because both call `render_word_page(card, token=...)`, the two targets are
byte-comparable on primary content by construction (P5-4 parity contract) —
tests/test_word_page.py locks it with no DB, and tests/test_static_cache.py's
sibling live check locks the card==API half.

Crawlability is the whole point (§5): every dictionary's panel is present in
the DOM at render time (the active one shown, the rest `hidden`), and a
`<noscript>` block shows all panels stacked. Progressive JS then hydrates the
tabs, the view-mode toggle, and the disclosures on top — a fetcher with no JS
still reads every entry.

Host-independence (RISKS.md R1/R5, CLAUDE.md citation-durability): the template
never hardcodes `samskrtam.ru`. Self/canonical links are built from the caller-
supplied `base` (default relative), so a page is identical whether served from
gasyoun.github.io/kosha or samskrtam.ru/kosha.
"""
import html
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO.parent / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1, slp1_to_devanagari, to_slp1  # noqa: E402


def _load_upasarga():
    """{root_slp1: [(combined, sense), …]} from the committed W6 dataset
    (data/gita/upasarga_semantics.tsv). Loaded once; a pure function of the
    committed file, so prerender ∥ SSR stay byte-identical."""
    import csv
    d = {}
    p = Path(__file__).resolve().parent.parent / "data" / "gita" / "upasarga_semantics.tsv"
    if not p.exists():
        return d
    with p.open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if not r["preverb"]:
                continue
            key = to_slp1(r["root"].replace("√", "").replace("-", "").strip())
            d.setdefault(key, []).append((r["combined"], r["sense"]))
    return d


_UPASARGA = _load_upasarga()


def _load_sense_freq():
    """{lemma_slp1: [{gloss, count, share, top_genre, top_share, nonsastra, est_count, …}]}
    from the committed MW layer of data/frequency/sense_frequency.tsv
    (H1453 + H1459 genre columns + H1588 estimated tier).

    Attested rows (provenance=attested / empty) drive the bar + share.
    Estimated rows (provenance=estimated) attach to the same sense_id/gloss as a
    separate count — never blended into the attested number (W3d / decision #8).
    Loaded once; pure function of the committed file so prerender ∥ SSR stay
    byte-identical (P5-4 parity, like _UPASARGA)."""
    import csv
    d = {}
    est = {}  # lemma -> sense_id|gloss -> estimated count
    p = Path(__file__).resolve().parent.parent / "data" / "frequency" / "sense_frequency.tsv"
    if not p.exists():
        return d
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["layer"] != "mw":
                continue
            prov = (r.get("provenance") or "attested").strip() or "attested"
            try:
                cnt = int(r["count_all"] or 0)
            except (ValueError, KeyError):
                continue
            lemma = r["lemma_slp1"]
            if prov == "estimated":
                key = r.get("sense_id") or r.get("sense_gloss") or ""
                est.setdefault(lemma, {})[key] = (
                    est.get(lemma, {}).get(key, 0) + cnt
                )
                continue
            try:
                share = float(r["lemma_share"] or 0)
            except (ValueError, KeyError):
                share = 0.0
            d.setdefault(lemma, []).append({
                "sense_id": r.get("sense_id") or "",
                "gloss": r["sense_gloss"], "count": cnt, "share": share,
                "top_genre": r.get("top_genre", ""),
                "top_share": float(r.get("top_genre_share") or 0),
                "nonsastra": int(r.get("count_nonsastra") or 0),
                "est_count": 0,
            })
    for lemma, senses in d.items():
        e_map = est.get(lemma) or {}
        for s in senses:
            s["est_count"] = (
                e_map.get(s["sense_id"], 0) or e_map.get(s["gloss"], 0)
            )
        senses.sort(key=lambda x: (-x["count"], x["gloss"]))
    # Lemmas with only estimated rows (no attested MW projection) — still show
    # estimated chips alone so the tier is not silently dropped.
    for lemma, e_map in est.items():
        if lemma in d:
            continue
        d[lemma] = [{
            "sense_id": sid, "gloss": sid, "count": 0, "share": 0.0,
            "top_genre": "", "top_share": 0.0, "nonsastra": 0,
            "est_count": n,
        } for sid, n in sorted(e_map.items(), key=lambda x: (-x[1], x[0]))]
    return d


_SENSE_FREQ = _load_sense_freq()
_SENSE_FREQ_CAP = 8  # senses shown per card; the rest fold into a "+N more" note
_GENRE_LABEL = {  # Renou genre key (dcs_text_genre.tsv) -> display label
    "rasasastra": "rasaśāstra", "ayurveda": "āyurveda", "jyotisa": "jyotiṣa",
    "arthasastra": "artha/kāma-śāstra", "veda": "Veda", "epic": "epic",
    "purana": "Purāṇa", "kavya": "kāvya", "katha": "narrative", "nataka": "drama",
    "dharmasastra": "dharmaśāstra", "darsana": "darśana", "vyakarana": "grammar",
    "kosa": "lexicon", "alamkara": "poetics", "tantra_yoga": "tantra/yoga",
    "stotra_bhakti": "stotra",
}

# Fixed chrome (H2670 / R1·R7·R12). Cologne dicts stay in card results;
# pwg_ru / mw_ru are joined at render time. Vote R5 ships them labeled
# AI-translated — it does not flip review_status and does not add Kochergina.
DICT_ORDER = ("mw", "pwg", "ap90", "pwg_ru", "mw_ru")
DICT_LABEL = {
    "mw": "MW", "pwg": "PWG", "ap90": "AP90",
    "pwg_ru": "pwg_ru", "mw_ru": "mw_ru",
}
DICT_FULL = {
    "mw": "Monier-Williams",
    "pwg": "Petersburger Wörterbuch (großes)",
    "ap90": "Apte 1890",
    "pwg_ru": "PWG Russian",
    "mw_ru": "MW Russian",
}
DICT_LANG = {
    "mw": "en", "ap90": "en",
    "pwg": "de",
    "pwg_ru": "ru", "mw_ru": "ru",
}
LANG_ORDER = ("en", "de", "ru")
LANG_LABEL = {"en": "EN", "de": "DE", "ru": "RU"}
LANG_DICTS = {
    "en": ("mw", "ap90"),
    "de": ("pwg",),
    "ru": ("pwg_ru", "mw_ru"),
}
COLOGNE_DICTS = frozenset({"mw", "pwg", "ap90"})
RU_DICTS = ("pwg_ru", "mw_ru")

BAND_CLASS = {1: "b1", 2: "b2", 3: "b3", 4: "b4", 5: "b5"}


def card_token(slp1: str) -> str:
    """Filesystem/URL-safe SLP1 encoding — exact twin of
    scripts/build_static_cache.py::card_token and ui/src/lib/cardToken.js.
    Keep [a-z0-9] verbatim, escape every other UTF-8 byte as _<hexbyte>."""
    out = []
    for b in slp1.encode("utf-8"):
        if (97 <= b <= 122) or (48 <= b <= 57):
            out.append(chr(b))
        else:
            out.append("_%02x" % b)
    return "".join(out)


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _plain(rendered_html: str, limit: int = 160) -> str:
    """Strip tags + collapse whitespace — for the <meta> description and the
    Gloss-mode teaser. Never inserted as HTML; always html.escape'd by callers."""
    text = _WS_RE.sub(" ", _TAG_RE.sub("", rendered_html or "")).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def entry_fields(entry):
    """The kosha-owned fields of a card entry, whatever card generation it is.

    W0C (H1945) moved `dict`/`L`/`headword`/`scan_url`/`rendered_html`/
    `evidence` into the Salt entry's `kosha` block. The static tier is deployed
    out of band, so a newly-shipped template can meet a card generated before
    that cut until the next Pages deploy — reading through this accessor keeps
    both readable instead of making the page 500 on a stale card.
    """
    block = entry.get("kosha")
    return block if isinstance(block, dict) else entry


def _group_by_dict(results):
    """Cologne dicts from the card, in DICT_ORDER. RU comes from the join."""
    grouped = {}
    for r in results:
        d = entry_fields(r).get("dict")
        if d in COLOGNE_DICTS:
            grouped.setdefault(d, []).append(r)
    return [(d, grouped[d]) for d in DICT_ORDER if d in grouped]


def _groups_for_page(results, ru_overlay):
    """Always emit the five chrome dicts; RU lists come from the join only."""
    grouped = {d: [] for d in DICT_ORDER}
    for d, entries in _group_by_dict(results):
        grouped[d] = entries
    overlay = ru_overlay or {}
    for d in RU_DICTS:
        grouped[d] = list(overlay.get(d) or [])
    return [(d, grouped[d]) for d in DICT_ORDER]


def _saru_strip(slp1, sr_strip):
    """One public-tier SanskritRussian line under the headword (H2680).

    Not a dictionary tab. Lemma layer wins, then surface. Honest miss
    when the public files are absent or the key is uncovered.
    """
    esc = html.escape
    if sr_strip is None:
        from kosha.api.sr_gloss import join_sr_strip
        sr_strip = join_sr_strip(slp1)
    text = (sr_strip or {}).get("text")
    if (sr_strip or {}).get("hit") and text:
        return (
            f'<p class="saru-strip" lang="ru">'
            f'<span class="saru-src">SanskritRussian</span> {esc(text)}</p>'
        )
    return (
        '<p class="saru-strip saru-miss">'
        "No SanskritRussian gloss for this lemma.</p>"
    )


def _headword_strip(slp1, deva, iast, band, band_label, n_dicts, ux=None, token=None):
    esc = html.escape
    band_cls = BAND_CLASS.get(band, "b5")
    extra = ""
    if ux:
        # H3457 staging organs (see app/word_page_ux.py). Variant b keeps the
        # strip clean and puts both organs in the study rail instead.
        from word_page_ux import study_badge, fav_button, gloss_switch
        v = ux["variant"]
        k = ux.get("slp1", slp1)
        if v == "a":
            extra = study_badge(k, v) + fav_button(k, deva, iast, token, v)
        elif v == "d":
            # H3480 R2: the Gloss/Full switch lives left of the heart, in the strip.
            extra = study_badge(k, v) + gloss_switch() + fav_button(k, deva, iast, token, v)
        elif v == "c":
            extra = fav_button(k, deva, iast, token, v)
    return (
        '<header class="hw-strip">'
        f'<span class="hw-deva" lang="sa">{esc(deva)}</span>'
        f'<span class="hw-iast">{esc(iast)}</span>'
        f'<span class="hw-key" title="SLP1 key">[{esc(slp1)}]</span>'
        f'<span class="band {band_cls}" title="{esc(band_label)}">band {band}</span>'
        f'<span class="ndicts">{n_dicts} dict{"s" if n_dicts != 1 else ""}</span>'
        # JS-hydrated grammar token (P4 Zaliznyak-style, e.g. m·8n*): filled from
        # the paradigm layer client-side so the static ∥ SSR primary content stays
        # byte-comparable (the paradigm is not part of the card payload). Empty in
        # the crawlable DOM, never fabricated.
        '<span class="gram" data-gram hidden></span>'
        f"{extra}"
        "</header>"
    )


def _view_toggle():
    # Hidden from no-JS readers (they get the full stacked content anyway).
    return (
        '<div class="view-toggle" role="radiogroup" aria-label="Detail level" hidden>'
        '<button type="button" data-view-set="gloss" role="radio" aria-checked="false">Gloss</button>'
        '<button type="button" data-view-set="full" role="radio" aria-checked="false">Full</button>'
        '<button type="button" data-view-set="adaptive" role="radio" aria-checked="true">Adaptive</button>'
        "</div>"
    )


def _entry_html(entry, ux=None):
    esc = html.escape
    fields = entry_fields(entry)
    scan = ""
    eid = ""
    if ux:
        # H3457 staging: stable per-entry anchor + a print anchor that names the
        # volume/column (PWG rebuilt through the H839 vol-col key).
        from word_page_ux import scan_anchor, entry_id
        scan, _url, _label = scan_anchor(fields, ux["variant"])
        _id = entry_id(fields)
        eid = f' id="{_id}"' if _id else ""
    elif fields.get("scan_url"):
        scan = (f'<a class="scan" href="{esc(fields["scan_url"])}" '
                f'target="_blank" rel="noopener">scan ↗</a>')
    status = (fields.get("review_status") or entry.get("review_status") or "").strip()
    badge = ""
    if status and status not in {"approved", "human_reviewed"}:
        badge = '<span class="chip ai-translated">AI-translated</span>'
    rendered = fields.get("rendered_html", "")
    if ux and fields.get("dict") == "pwg":
        # H3479 wave 2: hydrate literary-source `<ls>` citations into links
        # (PWG only; see app/ls_hydrate.py). Honest no-op when the two
        # sibling checkouts it reads are absent.
        from ls_hydrate import hydrate_pwg_ls
        rendered, _stats = hydrate_pwg_ls(rendered)
    # `rendered_html` is interpolated unescaped — it is HTML by contract. What
    # makes that safe is that it can only have come through
    # `kosha.api.sanitize` (W0C item 6); the serializer has no path that emits
    # unsanitized render output.
    return (
        f'<article class="dict-entry"{eid}>'
        f'<div class="entry-head"><span class="hw">{esc(fields.get("headword", ""))}</span>'
        f"{scan}{badge}</div>"
        f'<div class="rendered">{rendered}</div>'
        "</article>"
    )


def _empty_state(dict_id):
    esc = html.escape
    return f'<p class="ru-empty">No {esc(dict_id)} row for this lemma.</p>'


def _first_visible_dict(default_lang):
    dicts = LANG_DICTS.get(default_lang) or LANG_DICTS["en"]
    return dicts[0]


def _dict_tab(d, entries, active):
    esc = html.escape
    return (
        f'<button type="button" class="tab{" active" if active else ""}" '
        f'role="tab" aria-selected="{"true" if active else "false"}" '
        f'aria-controls="panel-{d}" id="tab-{d}" data-dict="{d}" '
        f'data-lang="{DICT_LANG[d]}" '
        f'title="{esc(DICT_FULL.get(d, d))}">{esc(DICT_LABEL.get(d, d.upper()))}'
        f'<span class="tab-n">{len(entries)}</span></button>'
    )


def _dict_panels(groups, default_lang="en", ux=None):
    """Two-level chrome: EN | DE | RU | All, then the dicts of that language."""
    esc = html.escape
    by_dict = {d: entries for d, entries in groups}
    if default_lang not in LANG_DICTS:
        default_lang = "en"
    first_dict = _first_visible_dict(default_lang)

    lang_tabs = []
    for lang in LANG_ORDER:
        active = lang == default_lang
        lang_tabs.append(
            f'<button type="button" class="tab{" active" if active else ""}" '
            f'role="tab" aria-selected="{"true" if active else "false"}" '
            f'id="tab-lang-{lang}" data-lang="{lang}" '
            f'title="{esc(LANG_LABEL[lang])}">{esc(LANG_LABEL[lang])}</button>'
        )
    n_all = sum(len(entries) for _, entries in groups)
    ids = " ".join(f"panel-{d}" for d in DICT_ORDER)
    lang_tabs.append(
        f'<button type="button" class="tab tab-all" role="tab" '
        f'aria-selected="false" aria-controls="{ids}" '
        f'id="tab-all" data-dict="all" data-lang="all" '
        f'title="Show every dictionary">'
        f'All<span class="tab-n">{n_all}</span></button>'
    )
    langbar = (
        f'<nav class="lang-tabs" role="tablist" aria-label="Languages">'
        f'{"".join(lang_tabs)}</nav>'
    )

    inner = []
    for lang, dicts in LANG_DICTS.items():
        hidden = "" if lang == default_lang else " hidden"
        tabs = [
            _dict_tab(d, by_dict.get(d) or [], active=(d == first_dict))
            for d in dicts
        ]
        inner.append(
            f'<nav class="dict-tabs" role="tablist" aria-label="Dictionaries" '
            f'data-lang="{lang}"{hidden}>{"".join(tabs)}</nav>'
        )

    panels = []
    for d in DICT_ORDER:
        entries = by_dict.get(d) or []
        lang = DICT_LANG[d]
        label = esc(DICT_FULL.get(d, d))
        body = "".join(_entry_html(e, ux) for e in entries) if entries else _empty_state(d)
        hidden = "" if d == first_dict else " hidden"
        panels.append(
            f'<section class="dict-panel" id="panel-{d}" role="tabpanel" '
            f'aria-labelledby="tab-{d}" data-dict="{d}" data-lang="{lang}"{hidden}>'
            f'<h2 class="dict-label">{label}</h2>{body}</section>'
        )
    return langbar + "".join(inner), "".join(panels)


def _evidence_block(ev):
    if not ev:
        return ""
    esc = html.escape
    rows = []
    band = ev.get("band", 5)
    rows.append(f'<li><b>Frequency band {band}</b> — {esc(ev.get("band_label", ""))}</li>')
    ca = ev.get("count_all")
    rows.append(f'<li>{esc(str(ca))} attestations in DCS</li>' if ca is not None
                else '<li>no attestation data</li>')
    fe = ev.get("first_era")
    if fe:
        rows.append(f'<li>first attested: {esc(str(fe))}</li>')
    ex = ev.get("example")
    ex_html = ""
    if ex and ex.get("sa"):
        work = f' — <cite>{esc(ex.get("work", "") or "")}</cite>' if ex.get("work") else ""
        ex_html = (f'<blockquote class="example" lang="sa">{esc(ex["sa"])}{work}</blockquote>')
    return (
        '<details class="disclosure evidence"><summary>Evidence</summary>'
        f'<ul class="ev-list">{"".join(rows)}</ul>{ex_html}</details>'
    )


def _paradigm_block(slp1, base):
    """Static paradigm affordance: a crawlable link into the inflection app,
    JS-hydrated to an inline "show all forms" table (P4 ParadigmTable) on top.
    No paradigm data is inlined (not in the card) so prerender ∥ SSR stay
    byte-comparable; the data-slp1 hook lets the client fetch + expand it."""
    esc = html.escape
    href = f"{base}inflect/?lemma={esc(slp1)}"
    return (
        f'<details class="disclosure paradigm" data-paradigm data-slp1="{esc(slp1)}">'
        '<summary>Paradigm (all forms)</summary>'
        f'<p class="para-fallback">Full inflection table: '
        f'<a href="{href}">open in the inflection lookup →</a></p>'
        "</details>"
    )


def _upasarga_block(slp1):
    """Root cards only: how preverbs (upasarga) shift this root's sense, from the
    W6 dataset. A pure function of slp1 + the committed TSV, so it is prerender ∥
    SSR byte-identical and crawlable (a static <details>, no host, no JS)."""
    variants = _UPASARGA.get(slp1)
    if not variants:
        return ""
    esc = html.escape
    items = "".join(
        f'<li><span class="upa-pv">{esc(c)}</span> — {esc(s)}</li>' for c, s in variants)
    return (
        '<details class="disclosure upasarga">'
        '<summary>Preverb senses (upasarga)</summary>'
        f'<ul class="upa-list">{items}</ul></details>'
    )


def _sense_frequency_block(slp1):
    """H1453: "N in this sense · M for the lemma" — per-MW-sense attested frequency from
    the WordSem-gold sidecar (data/frequency/sense_frequency.tsv, mw layer), LEFT-JOINed by
    lemma. A pure function of slp1 + the committed TSV, so prerender ∥ SSR are byte-identical
    and the page stays crawlable (a static <details>, no host, no JS). Returns '' for a lemma
    with no sense-frequency row (the LEFT-JOIN never drops such a lemma — it just omits the
    block). Two-tier badge per sense: an `attested` chip (populated on WordSem gold) and an
    `estimated` chip (empty in wave-1; wave-2 WSD lights it) — the two are never blended."""
    senses = _SENSE_FREQ.get(slp1)
    if not senses:
        return ""
    esc = html.escape
    total = sum(s["count"] for s in senses)
    total_est = sum(int(s.get("est_count") or 0) for s in senses)
    items = []
    for s in senses[:_SENSE_FREQ_CAP]:
        cnt, share = s["count"], s["share"]
        est = int(s.get("est_count") or 0)
        pct = round(share * 100)
        # wave-2 genre flags: expose corpus-composition bias in the DOM.
        flag = ""
        if cnt > 0 and s["nonsastra"] == 0:                       # sense never attested outside śāstra
            flag = ('<span class="chip warn" title="never attested outside technical śāstra '
                    '(alchemy/medicine/…) — a corpus-composition artefact, not general usage">'
                    'śāstra-only</span>')
        elif s["top_share"] >= 0.5 and s["top_genre"]:            # concentrated in one genre
            g = _GENRE_LABEL.get(s["top_genre"], s["top_genre"])
            flag = (f'<span class="chip genre" title="most tokens of this sense come from one '
                    f'genre — read the count as genre-relative">{round(s["top_share"]*100)}% {esc(g)}</span>')
        # H1588 W3d: light estimated chip only when mass exists; never add into attested.
        if est > 0:
            est_chip = (
                f'<span class="chip est" title="WSD estimate (MFS on untagged DCS tokens; '
                f'not blended with attested)"><b>{est}</b> estimated</span>'
            )
        else:
            est_chip = (
                '<span class="chip est" title="no WSD estimate for this sense"></span>'
            )
        items.append(
            '<li class="sf-item">'
            f'<span class="sf-gloss">{esc(s["gloss"])}</span>'
            f'<span class="sf-bar" aria-hidden="true"><span class="sf-fill" style="width:{pct}%"></span></span>'
            '<span class="sf-nums">'
            f'<span class="chip att"><b>{cnt}</b> in this sense</span>'
            f'{est_chip}'
            f'{flag}'
            f'<span class="sf-share">{pct}%</span>'
            '</span></li>'
        )
    more = len(senses) - _SENSE_FREQ_CAP
    more_html = (f'<li class="sf-more">+{more} more attested sense'
                 f'{"s" if more != 1 else ""}</li>') if more > 0 else ""
    est_head = (
        f' · <b>{total_est}</b> estimated (untagged MFS)' if total_est else ""
    )
    return (
        '<details class="disclosure sense-freq">'
        '<summary>Sense frequency</summary>'
        f'<p class="sf-head"><b>{total}</b> for the lemma · attested in DCS WordSem gold'
        f'{est_head} '
        '<span class="sf-legend"><span class="chip att">attested</span>'
        '<span class="chip est" title="WSD estimate — H1588">estimated</span></span></p>'
        f'<ul class="sf-list">{"".join(items)}{more_html}</ul>'
        '<p class="sf-foot">DCS over-samples technical śāstra (alchemy/medicine); '
        'a <span class="chip warn">śāstra-only</span> or genre chip marks a count that reflects '
        'corpus composition, not general Sanskrit. '
        'Estimated counts cover untagged DCS tokens via most-frequent-sense WSD '
        'and are never added into the attested figure.</p></details>'
    )


PAGE_CSS = """
:root{--fg:#1a1a1a;--muted:#6b7280;--border:#d7d7db;--accent:#7b2d26;
--card-bg:#fafafa;--head-bg:#f0f0f2;--hit-bg:#fdf3e7;--tag-bg:#ece7e0;
--tag-fg:#7b2d26;--page-bg:#fff;--b1:#7b2d26;--b2:#a05a2c;--b3:#4a7a3a;
--b4:#5a6b8c;--b5:#9aa0a6}
@media(prefers-color-scheme:dark){:root{--fg:#e8e8ea;--muted:#9aa0a6;
--border:#3a3a40;--accent:#e0a44a;--card-bg:#202024;--head-bg:#26262b;
--hit-bg:#3a3020;--tag-bg:#2c2c31;--tag-fg:#e0a44a;--page-bg:#161618;
--b1:#e0a44a;--b2:#d08a3a;--b3:#7bbf6a;--b4:#8fa4c8;--b5:#6b7078}}
*{box-sizing:border-box}
body{margin:0;background:var(--page-bg);color:var(--fg);
font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}
.word-page{max-width:52rem;margin:0 auto;padding:1.2rem 1rem 4rem}
.hw-strip{display:flex;gap:.7rem;align-items:baseline;flex-wrap:wrap;
border-bottom:1px solid var(--border);padding-bottom:.6rem}
.hw-deva{font-size:2rem}.hw-iast{font-size:1.2rem;color:var(--muted)}
.hw-key{font-family:monospace;font-size:.8rem;color:var(--muted)}
.band{font-size:.65rem;font-weight:700;padding:.12rem .45rem;border-radius:4px;
color:#fff;text-transform:uppercase}
.band.b1{background:var(--b1)}.band.b2{background:var(--b2)}
.band.b3{background:var(--b3)}.band.b4{background:var(--b4)}.band.b5{background:var(--b5)}
.ndicts,.gram{font-size:.72rem;color:var(--muted)}
.gram{font-family:monospace}
.saru-strip{margin:.4rem 0 0;font-size:.95rem;line-height:1.4}
.saru-strip .saru-src{font-size:.68rem;font-weight:700;letter-spacing:.04em;
text-transform:uppercase;color:var(--muted);margin-right:.45rem}
.saru-strip.saru-miss{font-size:.85rem;color:var(--muted)}
.view-toggle{display:inline-flex;margin:.7rem 0 0;border:1px solid var(--border);
border-radius:6px;overflow:hidden}
.view-toggle button{border:none;background:var(--page-bg);color:var(--muted);
padding:.3rem .7rem;cursor:pointer;font-size:.8rem}
.view-toggle button[aria-checked=true]{background:var(--head-bg);color:var(--fg);font-weight:600}
.lang-tabs,.dict-tabs{display:flex;gap:.35rem;flex-wrap:wrap;margin:.9rem 0 0;
border-bottom:1px solid var(--border)}
.dict-tabs{margin-top:.35rem}
.tab{border:1px solid var(--border);border-bottom:none;background:var(--card-bg);
color:var(--fg);padding:.4rem .8rem;cursor:pointer;border-radius:6px 6px 0 0;font-size:.9rem}
.tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.tab-all{margin-left:.35rem}
.tab-n{font-size:.65rem;opacity:.75;margin-left:.3rem}
.ru-empty{font-size:.9rem;color:var(--muted);margin:.6rem 0}
.chip.ai-translated{background:var(--hit-bg);color:var(--accent);font-weight:600;
margin-left:.45rem}
.dict-label{display:none;font:600 .85rem/1.3 system-ui,sans-serif;
margin:0 0 .6rem;color:var(--accent)}
.word-page.all-dicts .dict-label{display:block}
.word-page.all-dicts .dict-panel{border-top:1px solid var(--border);
padding-top:.9rem;margin-top:1.1rem}
.dict-panel{border:1px solid var(--border);border-top:none;padding:.4rem 1rem;
background:var(--card-bg)}
.dict-entry{border-top:1px solid var(--border);padding:.55rem 0}
.dict-entry:first-child{border-top:none}
.entry-head{display:flex;gap:.7rem;align-items:baseline;margin-bottom:.25rem}
.entry-head .hw{font-weight:600}
.scan{font-size:.8rem;color:var(--accent)}
.rendered{overflow-wrap:anywhere}
[data-view=gloss] .dict-entry:not(:first-child){display:none}
@media(max-width:640px){[data-view=adaptive] .dict-entry:not(:first-child){display:none}}
.disclosure{margin:.8rem 0 0;border:1px solid var(--border);border-radius:8px;
background:var(--card-bg);padding:.3rem .8rem}
.disclosure summary{cursor:pointer;font-weight:600;font-size:.9rem;padding:.3rem 0}
.upa-list{margin:.2rem 0 .4rem;padding-left:1.1rem;font-size:.9rem}
.upa-pv{font-weight:600}
.ev-list{margin:.2rem 0 .4rem;padding-left:1.1rem;font-size:.9rem}
.example{margin:.3rem 0;padding:.4rem .7rem;border-left:3px solid var(--accent);
background:var(--hit-bg);font-size:1.05rem}
.sf-head{margin:.2rem 0 .5rem;font-size:.85rem;color:var(--muted)}
.sf-head b{color:var(--fg)}
.sf-legend{margin-left:.5rem;font-size:.72rem}
.sf-list{list-style:none;margin:.2rem 0 .3rem;padding:0}
.sf-item{margin:.35rem 0}
.sf-gloss{display:block;font-size:.9rem;margin-bottom:.15rem}
.sf-bar{display:block;height:.5rem;background:var(--tag-bg);border-radius:3px;overflow:hidden}
.sf-fill{display:block;height:100%;background:var(--accent);border-radius:3px}
.sf-nums{display:flex;align-items:center;gap:.4rem;margin-top:.15rem;font-size:.8rem;flex-wrap:wrap}
.sf-share{color:var(--muted)}
.sf-more{font-size:.8rem;color:var(--muted);margin-top:.3rem;list-style:none}
.chip{display:inline-block;font-size:.7rem;padding:.05rem .4rem;border-radius:4px;line-height:1.5}
.chip.att{background:var(--tag-bg);color:var(--tag-fg)}
.chip.att b{color:var(--tag-fg)}
.chip.est{background:transparent;border:1px dashed var(--border);color:var(--muted);min-width:1.6rem}
.chip.genre{background:transparent;border:1px solid var(--b2);color:var(--b2)}
.chip.warn{background:var(--b1);color:#fff;font-weight:600}
.sf-foot{margin:.5rem 0 .2rem;font-size:.72rem;color:var(--muted);line-height:1.4}
.sf-foot .chip.warn{font-size:.66rem}
.wp-foot{margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--border);
font-size:.78rem;color:var(--muted)}
.wp-foot a{color:var(--accent)}
""".strip()


PAGE_JS = """
(function(){
 var VM='kosha_view_mode',root=document.documentElement;
 function setView(v){root.setAttribute('data-view',v);
  try{localStorage.setItem(VM,v)}catch(e){}
  document.querySelectorAll('[data-view-set]').forEach(function(b){
   b.setAttribute('aria-checked',b.getAttribute('data-view-set')===v?'true':'false')})}
 try{var s=localStorage.getItem(VM);if(s)root.setAttribute('data-view',s)}catch(e){}
 var vt=document.querySelector('.view-toggle');if(vt){vt.hidden=false;
  setView(root.getAttribute('data-view')||'adaptive');
  vt.addEventListener('click',function(e){var b=e.target.closest('[data-view-set]');
   if(b)setView(b.getAttribute('data-view-set'))})}
 var page=document.querySelector('.word-page');
 function markTabs(sel, attr, want){
  document.querySelectorAll(sel).forEach(function(x){
   var on=x.getAttribute(attr)===want;
   x.classList.toggle('active',on);
   x.setAttribute('aria-selected',on?'true':'false')})}
 function showLang(lang){
  var all=lang==='all';
  if(page){page.classList.toggle('all-dicts',all);page.setAttribute('data-lang',lang)}
  markTabs('.lang-tabs .tab','data-lang',lang);
  document.querySelectorAll('.dict-tabs').forEach(function(n){
   n.hidden=all || n.getAttribute('data-lang')!==lang});
  if(all){
   document.querySelectorAll('.dict-panel').forEach(function(p){p.hidden=false});
   document.querySelectorAll('.dict-tabs .tab').forEach(function(t){
    t.classList.remove('active');t.setAttribute('aria-selected','false')});
   return}
  var bar=document.querySelector('.dict-tabs[data-lang="'+lang+'"]');
  var first=bar && bar.querySelector('.tab');
  showDict(first?first.getAttribute('data-dict'):null)}
 function showDict(want){
  if(!want)return;
  if(page)page.classList.remove('all-dicts');
  markTabs('.dict-tabs .tab','data-dict',want);
  document.querySelectorAll('.dict-panel').forEach(function(p){
   p.hidden=p.getAttribute('data-dict')!==want})}
 document.querySelectorAll('.lang-tabs .tab').forEach(function(t){
  t.addEventListener('click',function(){showLang(t.getAttribute('data-lang'))})});
 document.querySelectorAll('.dict-tabs .tab').forEach(function(t){
  t.addEventListener('click',function(){showDict(t.getAttribute('data-dict'))})});
 var lang=(page && page.getAttribute('data-lang'))||'en';
 try{var nav=(navigator.language||'').toLowerCase();
  if(nav.indexOf('ru')===0)lang='ru'}catch(e){}
 showLang(lang)
})();
""".strip()


def render_word_page(card, *, token=None, base="../", data_version=None,
                     public_base="", include_doc=True, default_lang="en",
                     ru_overlay=None, sr_strip=None, ux=None):
    """Render one word page from a card (the /api/v1/lemma envelope shape).

    `card`      : {"query": {"key": slp1}, "results": [...], "data_version": ...}
    `token`     : card_token(slp1); computed if omitted.
    `base`      : URL prefix for in-site links to the site root that holds
                  inflect/ and browse/. Word pages always live under /w/ (both the
                  static prerender and the SSR route), so the default "../" is
                  correct everywhere; host-independent (never an absolute host).
    `public_base`: optional absolute origin for the JSON-LD/canonical (SEO only);
                  empty keeps everything relative (R1/R5 default).
    `include_doc`: wrap in <!doctype html>… (prerender). False returns just the
                  <main> fragment (SSR can embed it, tests compare the core).
    `default_lang`: first-paint language (`en` unless SSR saw `ru`).
    `ru_overlay`: optional `{pwg_ru, mw_ru}` entry lists; `None` joins the
                  sibling/fixture store. Pass `{}` to force the empty state.
    `sr_strip`: optional `{hit, text, layer}` for the SanskritRussian line;
                  `None` joins the public site-tier files.
    `ux`        : H3457 STAGING layer — `None` (default, the public page,
                  byte-identical to pre-H3457 output) or a variant letter /
                  `{"variant": "a"|"b"|"c"}` enabling the study badge,
                  favorites and print-scan anchors (app/word_page_ux.py).
                  Not on any public build until a human flips it
                  (docs/NOT_PUBLISHED_H3457_WPAGE_UX.md).
    """
    esc = html.escape
    if token is not None:
        # Cards store query.key case-folded for capitalised SLP1 lemmas
        # ("darma" for Darma, "rama" for rAma; kosha#433) — the token is the
        # exact key, so derive slp1 from it whenever a token is supplied.
        from word_page_ux import slp1_from_token
        slp1 = slp1_from_token(token)
    else:
        slp1 = card["query"]["key"]
        token = card_token(slp1)
    results = card.get("results", [])
    deva = slp1_to_devanagari(slp1)
    iast = from_slp1(slp1)
    if ru_overlay is None:
        from kosha.api.ru_join import join_ru
        ru_overlay = join_ru(slp1)
    groups = _groups_for_page(results, ru_overlay)
    n_dicts = sum(1 for _, entries in groups if entries)
    ev = entry_fields(results[0]).get("evidence") if results else None
    band = (ev or {}).get("band", 5)
    band_label = (ev or {}).get("band_label", "")
    if default_lang not in LANG_DICTS:
        default_lang = "en"

    if ux is not None and not isinstance(ux, dict):
        ux = {"variant": str(ux)}
    if ux:
        from word_page_ux import VARIANTS, DEFAULT_VARIANT
        if ux.get("variant") not in VARIANTS:
            ux = dict(ux, variant=DEFAULT_VARIANT)
        # slp1 is already token-derived above when a token is supplied, so
        # every UX lookup (core_rank, favorites key) uses the exact key.
        ux = dict(ux, slp1=slp1)

    tabbar, panels = _dict_panels(groups, default_lang=default_lang, ux=ux)
    strip = _headword_strip(slp1, deva, iast, band, band_label, n_dicts,
                            ux=ux, token=token)
    saru = _saru_strip(slp1, sr_strip)
    ux_css = ux_js = ux_pre = ux_rail = ux_foot = ""
    if ux:
        from word_page_ux import (ux_css as _ux_css, ux_js as _ux_js, study_badge,
                                  study_rail, footer_fav_link, flat_tabbar)
        v = ux["variant"]
        ux_css = "\n" + _ux_css(v)
        ux_js = "\n" + _ux_js(v)
        ux_foot = footer_fav_link(base)
        if v == "d":
            # H3480 R1/R4/R5: three header rows — strip · SanskritRussian · ONE
            # flat dictionary tab row. The language row, the per-language rows and
            # the RU sub-row are gone; the toggle moved into the strip.
            tabbar = flat_tabbar(groups, _first_visible_dict(default_lang))
        k = ux["slp1"]
        if v == "c":
            ux_pre = study_badge(k, v)          # the rank line under the strip
        elif v == "b":
            ux_rail = study_rail(k, deva, iast, token, groups)

    # <noscript>: show every panel stacked (CSS reveals them), hide the tab bar.
    noscript = ("<noscript><style>.dict-panel[hidden]{display:block!important}"
                ".lang-tabs,.dict-tabs,.view-toggle{display:none!important}</style></noscript>")

    body_core = (
        ("" if (ux and ux["variant"] == "d") else _view_toggle())
        + noscript
        + tabbar
        + panels
        + _evidence_block(ev)
        + _sense_frequency_block(slp1)
        + _paradigm_block(slp1, base)
        + _upasarga_block(slp1)
    )
    # Variant b's rail is a direct child of <main> (grid-placed by CSS, no
    # wrapper div): entry rendered_html is Cologne markup and may close a
    # wrapper early, which would spill the panels into the rail column.
    main = (
        '<main class="word-page" data-slp1="%s" data-lang="%s">' % (
            esc(slp1), esc(default_lang))
        + strip
        + ux_pre
        + ux_rail
        + saru
        + body_core
        + '<footer class="wp-foot">Gasuns Sanskrit Dictionary · '
        + '<a href="%sinflect/">inflection lookup</a> · ' % esc(base)
        + '<a href="%sbrowse/">browse</a> · ' % esc(base)
        + ux_foot
        + 'entries from MW, PWG &amp; Apte (Cologne), rendered verbatim.</footer>'
        + "</main>"
    )
    if not include_doc:
        return main

    dv = data_version or card.get("data_version", "")
    desc = esc(_plain(entry_fields(results[0])["rendered_html"]) if results else iast)
    title = f"{esc(deva)} {esc(iast)} — Sanskrit dictionary | kosha"
    canonical = (f'<link rel="canonical" href="{esc(public_base)}/w/{esc(token)}.html">'
                 if public_base else "")
    return (
        "<!doctype html>\n"
        f'<html lang="sa" data-view="adaptive"><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{title}</title>"
        f'<meta name="description" content="{desc}">'
        f'<meta name="data-version" content="{esc(dv)}">'
        f"{canonical}"
        f"<style>{PAGE_CSS}{ux_css}</style>"
        "</head><body>"
        f"{main}"
        f"<script>{PAGE_JS}{ux_js}</script>"
        "</body></html>\n"
    )
