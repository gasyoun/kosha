"""Tests for app/scan_resolver.py's PWG multi-volume disambiguation (H839,
13-07-2026). Cologne's servepdf.php has no vol=/volume= GET parameter (verified
against csl-apidev/parm.php + servepdfClass.php source, and live against the
production endpoint) -- for PWG the volume must be folded into `page` itself
as "{vol}-{page:04d}", matching pdffiles.txt's own keys. See scan_resolver.py's
module docstring for the full live-verification trail.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from scan_resolver import scan_url  # noqa: E402


def test_pwg_requires_vol_and_folds_it_into_page():
    url = scan_url("pwg", 1, 1)
    assert url == (
        "https://sanskrit-lexicon.uni-koeln.de/scans/PWGScan/2020/"
        "web/webtc/servepdf.php?page=1-0001"
    )


def test_pwg_different_volumes_yield_different_urls():
    vol1 = scan_url("pwg", 1, 1)
    vol7 = scan_url("pwg", 1, 7)
    assert vol1 != vol7
    assert vol1.endswith("page=1-0001")
    assert vol7.endswith("page=7-0001")


def test_pwg_without_vol_returns_none_rather_than_ambiguous_link():
    # Before H839 this silently built page=1 -> Cologne default-volume-1
    # ambiguity; now it refuses to emit a link it can't disambiguate.
    assert scan_url("pwg", 1, None) is None


def test_pwg_page_is_zero_padded_to_four_digits():
    assert scan_url("pwg", 513, 2).endswith("page=2-0513")


def test_single_volume_dicts_use_bare_page_and_ignore_vol():
    assert scan_url("mw", 513) == (
        "https://sanskrit-lexicon.uni-koeln.de/scans/MWScan/2020/"
        "web/webtc/servepdf.php?page=513"
    )
    assert scan_url("ap90", 42, None) == (
        "https://sanskrit-lexicon.uni-koeln.de/scans/AP90Scan/2020/"
        "web/webtc/servepdf.php?page=42"
    )


def test_unknown_dict_returns_none():
    assert scan_url("zzz", 1) is None


def test_none_page_returns_none():
    assert scan_url("pwg", None, 1) is None
