"""The docs site (wiki/ → docs-site/, ZettelkastenWiki pilot) must satisfy
the package's full invariant harness and stay in sync with the committed
output."""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

zk = pytest.importorskip("zettelkastenwiki")

from build_docs_site import CONFIG  # noqa: E402

from zettelkastenwiki import publish, testing  # noqa: E402


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("docs_site")
    publish(CONFIG, out)
    return out


def test_invariant_harness(site):
    testing.run_all(site, CONFIG)


def test_expected_pages_exist(site):
    for rel in (
        "index.html",
        "docs/what-is-kosha/index.html",
        "docs/positioning/index.html",
        "docs/roadmap/index.html",
        "faq/what-works-today/index.html",
        "faq/data-licensing/index.html",
    ):
        assert (site / rel).exists(), f"missing {rel}"


def test_committed_output_is_current(site):
    """docs-site/ is committed for legacy Pages; fail if someone edited wiki/
    without rebuilding (python scripts/build_docs_site.py)."""
    committed = REPO / "docs-site"
    if not committed.exists():
        pytest.skip("docs-site/ not built yet")
    fresh = {p.relative_to(site).as_posix() for p in site.rglob("*.html")}
    on_disk = {p.relative_to(committed).as_posix() for p in committed.rglob("*.html")}
    assert fresh == on_disk, "docs-site/ page set differs — rerun scripts/build_docs_site.py"
    for rel in sorted(fresh):
        a = (site / rel).read_text(encoding="utf-8")
        b = (committed / rel).read_text(encoding="utf-8")
        assert a == b, f"docs-site/{rel} stale — rerun scripts/build_docs_site.py"
