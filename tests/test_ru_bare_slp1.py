"""H3490 — bare SLP1 quotations in the RU overlay are transliterated on the page.

MG 25-08-2026 ("RU still showed raw"): 116 of 1,063 pwg_ru entries on the H3457
sample quote Sanskrit as bare SLP1 with Vedic accent marks and no `{#…#}`
wrapper. `ru_bare_slp1_pass` wraps such runs as sdata IAST; Cyrillic, tags,
`<span class="ls">` citations, trailing-period abbreviations and ALL-CAPS
tokens must never be touched.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kosha.api.ru_join import ru_bare_slp1_pass, _slp1_anchor  # noqa: E402


def test_accented_vedic_run():
    out = ru_bare_slp1_pass('о движении: tena^ gacCa parasta\\ram <span class="ls">ṚV. 10,155,3.</span> pa\\raH')
    assert out == ('о движении: <span class="sdata">tena gaccha parastaram</span> '
                   '<span class="ls">ṚV. 10,155,3.</span> <span class="sdata">paraḥ</span>')


def test_classical_capitals_inside_word():
    out = ru_bare_slp1_pass("tena (mArgeRa) gacCan M. 4,178.")
    assert '<span class="sdata">mārgeṇa</span>' in out and '<span class="sdata">gacchan</span>' in out
    assert "M. 4,178." in out


def test_untouched_abbreviations_citations_cyrillic_and_existing_sdata():
    src = ('Special-Tempora четырьмя способами: I. <span class="sdata">gamati</span> NAIGH. 2,14. '
           'vgl. med. simpl. u. s. w. MBH. 1,4312.')
    assert ru_bare_slp1_pass(src) == src


def test_anchor_rules():
    assert _slp1_anchor("gacCa") and _slp1_anchor("tena^") and _slp1_anchor("Sf\\to")
    assert not _slp1_anchor("NAIGH.") and not _slp1_anchor("MBH") and not _slp1_anchor("vgl.")
    assert not _slp1_anchor("tena")  # plain lowercase is only pulled in as a neighbour


def test_avagraha_run_stays_one_span():
    out = ru_bare_slp1_pass("yatpa^rA\\vato 'ja^gannU\\taye^ 1,130,9.")
    assert out.count('<span class="sdata">') == 1 and "1,130,9." in out
