"""kosha — citation payload (RISKS.md R1 Commitment 1, ARCHITECTURE.md A2).

The `cite` object on a sense must let a scholar's 2026 citation still resolve in
a 2028 browser (R1). It therefore carries, beyond the formatted `text`:

- **resolution_url** — a browser-resolvable URL that resolves the *pinned*
  version. The sense id embeds `@{data_version}`, so the URL is just the sense
  endpoint over that id; the API serves the archived version (app/versions.py)
  when it differs from the current build. This is the "works in a browser"
  path T-UC10 forces. Its host is the durable API mirror, never samskrtam.ru
  (R5: citations must not depend on the server host).
- **release_asset** — the durable, never-deleted GitHub release-asset permalink
  for that version's data dump (R1 Commitment 3). `None` for `*-dev` builds,
  which are explicitly not citable (they ship no release).
- **bibtex** / **csl_json** — machine-citation forms pinned to the version.
"""

REPO = "gasyoun/kosha"
DICT_TITLES = {
    "mw": "Monier-Williams Sanskrit-English Dictionary",
    "pwg": "Böhtlingk & Roth, Sanskrit-Wörterbuch (Petersburg, large)",
    "ap90": "Apte, The Practical Sanskrit-English Dictionary (1890)",
}


def _is_citable(version: str) -> bool:
    return bool(version) and not version.endswith("-dev")


def release_asset_url(version: str):
    if not _is_citable(version):
        return None
    return f"https://github.com/{REPO}/releases/download/data-{version}/senses.sqlite"


def cite_object(dict_code: str, L: str, sense_n: int, version: str,
                public_base: str, headword: str | None = None) -> dict:
    text = f"{dict_code}.{L}.{sense_n}@{version}"
    resolution_url = f"{public_base.rstrip('/')}/api/v1/sense/{text}"
    title = DICT_TITLES.get(dict_code, dict_code.upper())
    hw = headword or ""
    bibtex = (
        f"@misc{{kosha_{dict_code}_{str(L).replace('.', '_')}_{sense_n},\n"
        f"  title = {{{hw} (sense {sense_n}), {title}}},\n"
        f"  howpublished = {{Gasuns Sanskrit Dictionary (kosha), sense {text}}},\n"
        f"  note = {{Version {version}}},\n"
        f"  url = {{{resolution_url}}}\n"
        f"}}"
    )
    csl_json = {
        "id": text,
        "type": "entry-dictionary",
        "title": f"{hw} (sense {sense_n})".strip(),
        "container-title": title,
        "version": version,
        "URL": resolution_url,
    }
    return {
        "text": text,
        "resolution_url": resolution_url,
        "release_asset": release_asset_url(version),
        "bibtex": bibtex,
        "csl_json": csl_json,
    }
