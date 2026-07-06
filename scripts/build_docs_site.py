"""Build the project docs site from wiki/ — ZettelkastenWiki Wave-3 pilot #1.

The generated site is COMMITTED to docs-site/ (GitHub Pages serves this repo's
main branch root via the legacy builder, so /kosha/docs-site/ is live once
merged). Additive by design: it does not touch the P2 static-cache tier or
the Pages configuration.

Rebuild after editing wiki/:

    python scripts/build_docs_site.py            # → docs-site/
    python scripts/build_docs_site.py <out_dir>  # → elsewhere (tests use this)
"""

from __future__ import annotations

import sys
from pathlib import Path

from zettelkastenwiki import GroupSpec, SiteConfig, publish

REPO = Path(__file__).resolve().parent.parent

CONFIG = SiteConfig(
    base_url="https://gasyoun.github.io/kosha/docs-site",
    site_name="Gasuns Sanskrit Dictionary — docs",
    org_name="Gasuns Sanskrit Dictionary",
    org_url="https://github.com/gasyoun/kosha",
    author="Mārcis Gasūns",
    language="en",
    wiki_root=REPO / "wiki",
    groups=(
        GroupSpec(name="docs", nav_label="Project", home_style="cards", jsonld_type="article"),
        GroupSpec(name="faq", nav_label="FAQ", home_style="accordion", jsonld_type="faq"),
    ),
    seo_title_suffix=" — Gasuns Sanskrit Dictionary",
    default_cta_primary=("Repository on GitHub", "https://github.com/gasyoun/kosha"),
    default_cta_secondary=("Data & tools directory", "https://gasyoun.github.io/kosha/directory/"),
    home_title="Gasuns Sanskrit Dictionary — project docs",
    home_description=(
        "Project documentation for the translator-first Sanskrit dictionary: "
        "what it is, the P1–P7 roadmap, honest status, data licensing and citability."
    ),
    footer_extra_html=(
        '<a href="https://github.com/gasyoun/kosha">GitHub</a> · '
        '<a href="https://gasyoun.github.io/kosha/directory/">Data &amp; tools directory</a> · '
        '<a href="https://gasyoun.github.io/kosha/features/">Features Index</a>'
    ),
)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs-site"
    publish(CONFIG, out)
    print(f"Docs site built at {out}")
