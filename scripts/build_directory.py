"""Build the public Sanskrit-NLP data + tools directory page for the kosha site.

Renders one static page (`directory/index.html`, served at
https://gasyoun.github.io/kosha/directory/) from two manifests, which stay the
single source of truth — no dataset/tool facts are hand-copied into HTML:

    data/manifest/datasets.json        — our derived datasets (public + restricted)
    data/manifest/external_tools.json  — curated external stacks (call, don't clone)

The page carries schema.org `Dataset` JSON-LD per PUBLIC dataset (the lever that
lets Google Dataset Search / Yandex index them) hung off a stable Organization
`@id` spine, per the org SEO playbook P0 tier.

Rebuild after editing either manifest:

    python scripts/build_directory.py            # -> directory/
    python scripts/build_directory.py <out_dir>  # -> elsewhere (tests)

Public tier only: this page must never link a private repo, a restricted
download URL, or an unpublished paper title. Restricted datasets are listed as
"available on request / in preparation" with no link.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO / "data" / "manifest"

SITE = "https://gasyoun.github.io/kosha"
DIRECTORY_URL = f"{SITE}/directory/"
ORG_ID = f"{SITE}/#org"
WEBSITE_ID = f"{SITE}/#website"
GITHUB = "https://github.com/gasyoun/kosha"
DATA_LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def human_size(n: int | None) -> str:
    if not n:
        return ""
    units = ["B", "KB", "MB", "GB"]
    f = float(n)
    for u in units:
        if f < 1024 or u == units[-1]:
            return f"{f:.0f} {u}" if u == "B" else f"{f:.1f} {u}"
        f /= 1024
    return f"{n}"


def download_url(ds: dict) -> str | None:
    """Public released dataset -> direct release-asset URL; public discovery-only
    dataset -> its source repo; restricted -> None (never linked)."""
    if ds.get("tier") != "public":
        return None
    rel = ds.get("in_release")
    asset = ds.get("release_asset")
    if rel and asset:
        return f"{GITHUB}/releases/download/{rel}/{asset}"
    # public but not in a kosha release -> already public in its source repo
    return ds.get("source_repo")


# --------------------------------------------------------------------------- #
# JSON-LD (SEO playbook P0: @id spine + Dataset per public asset)
# --------------------------------------------------------------------------- #
def jsonld(datasets: list[dict]) -> str:
    graph: list[dict] = [
        {
            "@type": "Organization",
            "@id": ORG_ID,
            "name": "Gasuns Sanskrit Dictionary",
            "url": GITHUB,
            "sameAs": [GITHUB],
        },
        {
            "@type": "WebSite",
            "@id": WEBSITE_ID,
            "url": SITE,
            "name": "Gasuns Sanskrit Dictionary",
            "inLanguage": "en",
            "publisher": {"@id": ORG_ID},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Data & tools directory"},
            ],
        },
    ]
    for ds in datasets:
        if ds.get("tier") != "public":
            continue
        url = download_url(ds)
        node: dict = {
            "@type": "Dataset",
            "name": ds["title"],
            "description": (ds.get("notes") or ds.get("keying") or ds["title"]),
            "license": DATA_LICENSE_URL,
            "isAccessibleForFree": True,
            "creator": {"@id": ORG_ID},
            "publisher": {"@id": ORG_ID},
            "includedInDataCatalog": {
                "@type": "DataCatalog",
                "name": "kosha Sanskrit data-hub",
                "url": DIRECTORY_URL,
            },
        }
        if ds.get("keying"):
            node["keywords"] = ["Sanskrit", "computational linguistics", ds["id"]]
        if url:
            node["distribution"] = {
                "@type": "DataDownload",
                "encodingFormat": ds.get("format", "tsv"),
                "contentUrl": url,
            }
        graph.append(node)
    doc = {"@context": "https://schema.org", "@graph": graph}
    # no flags -> "/" escaped to "\/", safe inside <script type=application/ld+json>
    return json.dumps(doc, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------- #
# HTML rendering (server-side from the manifests; no client fetch)
# --------------------------------------------------------------------------- #
def dataset_card(ds: dict) -> str:
    public = ds.get("tier") == "public"
    url = download_url(ds)
    meta = []
    if ds.get("rows"):
        meta.append(f"{ds['rows']:,} rows")
    if ds.get("size_bytes"):
        meta.append(human_size(ds["size_bytes"]))
    if ds.get("format"):
        meta.append(esc(ds["format"].upper()))
    meta_html = " · ".join(esc(m) for m in meta)

    if public and url and ds.get("release_asset"):
        action = f'<a class="dl" href="{esc(url)}">Download ↓</a>'
        badge = '<span class="badge pub">public</span>'
    elif public and url:
        action = f'<a class="dl ghost" href="{esc(url)}">In source repo ↗</a>'
        badge = '<span class="badge pub">public</span>'
    else:
        action = '<span class="dl none">available on request / in preparation</span>'
        badge = '<span class="badge res">restricted</span>'

    consumers = ds.get("consumers") or []
    cons_html = ""
    if consumers:
        chips = "".join(f'<span class="chip">{esc(c)}</span>' for c in consumers[:5])
        cons_html = f'<div class="chips">{chips}</div>'

    return f"""    <article class="card">
      <div class="card-h">
        <h3>{esc(ds['title'])}</h3>
        {badge}
      </div>
      <p class="key">{esc(ds.get('keying', ''))}</p>
      <p class="meta">{meta_html}</p>
      {cons_html}
      <div class="card-f">{action}</div>
    </article>"""


def tool_card(t: dict) -> str:
    lic = esc(t.get("license", ""))
    return f"""    <article class="card tool">
      <div class="card-h">
        <h3><a href="{esc(t['homepage'])}">{esc(t['name'])}</a></h3>
        <span class="badge ext">external</span>
      </div>
      <p class="org">{esc(t.get('org', ''))}</p>
      <p class="key">{esc(t.get('what_it_does', ''))}</p>
      <p class="rel"><b>Our relation:</b> {esc(t.get('our_relation', ''))}</p>
      <div class="card-f">
        <a class="dl ghost" href="{esc(t.get('api_url', t['homepage']))}">Call / docs ↗</a>
        <span class="lic">{lic}</span>
      </div>
    </article>"""


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{directory_url}">
<meta name="description" content="{desc}">
<meta property="og:title" content="Sanskrit NLP Data &amp; Tools Directory — kosha">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<title>Sanskrit NLP Data &amp; Tools Directory — Gasuns Sanskrit Dictionary</title>
<script type="application/ld+json">
{jsonld}
</script>
<style>
  :root{{
    --leaf:#F4EEE1;--leaf-2:#EDE5D3;--leaf-3:#E4D9C1;
    --ink:#241B12;--ink-2:#4A3D2E;--ink-3:#6E5F4B;
    --lapis:#2B4A8B;--lapis-soft:#e7ecf6;--haldi:#B0761B;
    --live:#3F7D4E;--live-bg:#e6efe7;--res:#9a5b2a;--res-bg:#f4ecda;--ext-bg:#e9edf1;--ext:#5A6B82;
    --serif:"Palatino Linotype","Book Antiqua",Palatino,Georgia,"Times New Roman",serif;
    --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:"SFMono-Regular","Cascadia Code",Consolas,"Liberation Mono",monospace;
    --maxw:1180px;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--leaf);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;
    background-image:radial-gradient(circle at 12% -8%,#faf6ec 0,transparent 46%),radial-gradient(circle at 100% 0,#efe7d5 0,transparent 40%);}}
  a{{color:var(--lapis);text-decoration:none}}
  a:hover{{text-decoration:underline;text-underline-offset:2px}}
  .wrap{{max-width:var(--maxw);margin:0 auto;padding:0 22px}}
  header.top{{border-bottom:1px solid var(--leaf-3);position:relative;overflow:hidden}}
  header.top .deva{{position:absolute;right:-1vw;top:50%;transform:translateY(-50%);font-family:var(--serif);
    font-size:clamp(120px,20vw,260px);color:#000;opacity:.045;line-height:.8;user-select:none;pointer-events:none}}
  .masthead{{padding:46px 0 30px;position:relative;z-index:1}}
  .eyebrow{{font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:var(--haldi);font-weight:700}}
  h1{{font-family:var(--serif);font-weight:600;font-size:clamp(30px,5vw,50px);line-height:1.04;margin:.28em 0 .12em;
    letter-spacing:-.01em;max-width:20ch}}
  .lede{{font-size:17px;color:var(--ink-2);max-width:64ch;margin:.5em 0 0}}
  .tallies{{display:flex;flex-wrap:wrap;gap:8px 10px;margin-top:22px}}
  .tally{{display:flex;align-items:baseline;gap:7px;background:var(--leaf-2);border:1px solid var(--leaf-3);border-radius:2px;padding:8px 13px}}
  .tally b{{font-family:var(--serif);font-size:21px;font-weight:700;font-variant-numeric:tabular-nums;color:var(--lapis)}}
  .tally span{{font-size:12.5px;color:var(--ink-3)}}
  .nav{{display:flex;gap:14px;flex-wrap:wrap;margin-top:18px;font-size:13.5px}}
  section.cat{{padding:38px 0 8px}}
  h2{{font-family:var(--serif);font-weight:600;font-size:26px;margin:0 0 4px;border-bottom:2px solid var(--haldi);display:inline-block;padding-bottom:3px}}
  .sub{{color:var(--ink-3);font-size:13.5px;margin:6px 0 20px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
  .card{{background:var(--leaf-2);border:1px solid var(--leaf-3);border-radius:5px;padding:16px 17px;display:flex;flex-direction:column}}
  .card-h{{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}}
  .card h3{{font-family:var(--serif);font-size:18px;font-weight:600;margin:0 0 2px;line-height:1.2}}
  .badge{{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;border-radius:3px;padding:3px 8px;white-space:nowrap}}
  .badge.pub{{background:var(--live-bg);color:var(--live)}}
  .badge.res{{background:var(--res-bg);color:var(--res)}}
  .badge.ext{{background:var(--ext-bg);color:var(--ext)}}
  .org{{font-size:12.5px;color:var(--haldi);font-weight:600;margin:0 0 6px}}
  .key{{font-size:13.5px;color:var(--ink-2);margin:2px 0 8px}}
  .rel{{font-size:12.5px;color:var(--ink-3);margin:0 0 8px}}
  .meta{{font-size:12px;color:var(--ink-3);font-variant-numeric:tabular-nums;margin:0 0 8px;font-family:var(--mono)}}
  .chips{{display:flex;flex-wrap:wrap;gap:5px;margin:0 0 10px}}
  .chip{{font-size:11px;background:var(--leaf);border:1px solid var(--leaf-3);border-radius:10px;padding:2px 9px;color:var(--ink-3)}}
  .card-f{{margin-top:auto;display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
  .dl{{font-weight:600;font-size:13.5px;background:var(--lapis);color:#fff;border-radius:4px;padding:7px 14px}}
  .dl:hover{{text-decoration:none;background:#213a70}}
  .dl.ghost{{background:transparent;color:var(--lapis);border:1px solid var(--lapis)}}
  .dl.ghost:hover{{background:var(--lapis-soft)}}
  .dl.none{{background:transparent;color:var(--ink-3);font-weight:500;font-style:italic;font-size:12.5px;padding:0}}
  .lic{{font-size:11.5px;color:var(--ink-3);font-family:var(--mono)}}
  footer{{border-top:1px solid var(--leaf-3);margin-top:44px;padding:26px 0 40px;color:var(--ink-3);font-size:13px}}
  footer a{{color:var(--lapis)}}
</style>
</head>
<body>
<header class="top">
  <div class="deva">कोश</div>
  <div class="wrap masthead">
    <div class="eyebrow">Gasuns Sanskrit Dictionary · the Sanskrit data-hub</div>
    <h1>Sanskrit NLP Data &amp; Tools Directory</h1>
    <p class="lede">A single curated entry point for Sanskrit computational linguistics: our openly-licensed derived datasets (downloadable), plus the external stacks and APIs the project builds on — what each does, how to call it, and its license.</p>
    <div class="tallies">
      <div class="tally"><b>{n_pub}</b><span>public datasets</span></div>
      <div class="tally"><b>{n_res}</b><span>restricted (on request)</span></div>
      <div class="tally"><b>{n_tools}</b><span>external tools &amp; stacks</span></div>
    </div>
    <div class="nav">
      <a href="#datasets">↓ Our datasets</a>
      <a href="#tools">↓ External tools</a>
      <a href="{github}">Repository</a>
      <a href="{site}/features/">Features Index</a>
    </div>
  </div>
</header>

<main class="wrap">
  <section class="cat" id="datasets">
    <h2>Our datasets</h2>
    <p class="sub">Derived from the Cologne Digital Sanskrit Dictionaries and the DCS corpus. Public assets are CC BY-SA 4.0, downloadable from the <a href="{github}/releases">kosha data releases</a>. Rendered from <a href="{github}/blob/main/data/manifest/datasets.json">datasets.json</a> — the single machine-readable source.</p>
    <div class="grid">
{public_cards}
    </div>
    <h2 style="margin-top:34px;font-size:21px">Restricted &amp; in preparation</h2>
    <p class="sub">Rights-encumbered or unbackuped local-only assets — listed for discovery; available on request as rights clear.</p>
    <div class="grid">
{restricted_cards}
    </div>
  </section>

  <section class="cat" id="tools">
    <h2>External tools &amp; stacks</h2>
    <p class="sub">Call these, don't clone them. Rendered from <a href="{github}/blob/main/data/manifest/external_tools.json">external_tools.json</a>.</p>
    <div class="grid">
{tool_cards}
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <p>Part of the <a href="{github}">Gasuns Sanskrit Dictionary (kosha)</a> — the Cologne Digital Sanskrit Dictionaries data-hub. Datasets CC BY-SA 4.0. Generated from the data manifests; do not hand-edit this page.</p>
    <p>Dr. Mārcis Gasūns · <a href="{site}/features/">Features Index</a> · <a href="{site}/questions/">Questions</a> · <a href="{site}/docs-site/">Docs</a></p>
  </div>
</footer>
</body>
</html>
"""


def build(out_dir: Path) -> Path:
    datasets = json.loads((MANIFEST_DIR / "datasets.json").read_text(encoding="utf-8"))["datasets"]
    tools = json.loads((MANIFEST_DIR / "external_tools.json").read_text(encoding="utf-8"))["tools"]

    public = [d for d in datasets if d.get("tier") == "public"]
    restricted = [d for d in datasets if d.get("tier") != "public"]

    desc = (
        f"{len(public)} openly-licensed Sanskrit datasets (downloadable) plus "
        f"{len(tools)} external NLP tools and APIs — the first curated directory for Sanskrit computational linguistics."
    )

    page = PAGE.format(
        directory_url=DIRECTORY_URL,
        desc=esc(desc),
        jsonld=jsonld(datasets),
        site=SITE,
        github=GITHUB,
        n_pub=len(public),
        n_res=len(restricted),
        n_tools=len(tools),
        public_cards="\n".join(dataset_card(d) for d in public),
        restricted_cards="\n".join(dataset_card(d) for d in restricted),
        tool_cards="\n".join(tool_card(t) for t in tools),
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "directory"
    written = build(out_dir)
    print(f"Directory page built at {written}")
