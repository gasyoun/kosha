"""kosha — encoding auto-detect + output formatting.

All conversion logic is delegated to sanskrit-util (SHARED_CODE.md family #1
— IAST<->SLP1<->Devanagari, single org source). This module adds only the
"auto" input-scheme sniffer and the SLP1->HK output map, neither of which
sanskrit-util exposes (its public API is IAST/SLP1/Devanagari only).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"))
from sanskrit_util import to_slp1, from_slp1, deva_to_slp1, iast_to_devanagari  # noqa: E402

_DEVA_RE = re.compile(r"[ऀ-ॿ]")
_IAST_DIACRITICS_RE = re.compile(r"[āīūṛṝḷḹṃṁḥṅñṭḍṇśṣḻ]")


def detect_scheme(text: str) -> str:
    """auto -> 'deva' | 'iast' | 'slp1'. HK is not distinguishable from bare-ASCII
    SLP1 without a dictionary lookup (both are plain ASCII letters); text with no
    diacritics and no Devanagari defaults to 'slp1' per ARCHITECTURE.md's
    "SLP1 is the internal key everywhere" — a known limitation for HK-only input
    that happens to use SLP1-reserved uppercase letters differently (documented,
    not silently wrong: such queries still resolve if they parse as valid SLP1)."""
    if _DEVA_RE.search(text):
        return "deva"
    if _IAST_DIACRITICS_RE.search(text.lower()):
        return "iast"
    return "slp1"


def to_slp1_auto(text: str, scheme: str = "auto") -> str:
    if scheme == "auto":
        scheme = detect_scheme(text)
    if scheme == "slp1":
        return text
    if scheme == "deva":
        return deva_to_slp1(text)
    if scheme in ("iast", "hk"):
        return to_slp1(text)  # HK input: best-effort via the IAST table (documented gap)
    raise ValueError(f"unknown scheme: {scheme}")


_SLP1_TO_HK = {
    "A": "A", "I": "I", "U": "U", "f": "R", "F": "RR", "x": "lR", "X": "lRR",
    "E": "ai", "O": "au", "M": "M", "H": "H",
    "K": "kh", "G": "gh", "N": "G", "C": "ch", "J": "jh", "Y": "J",
    "w": "T", "W": "Th", "q": "D", "Q": "Dh", "R": "N",
    "T": "th", "D": "dh", "P": "ph", "B": "bh",
    "S": "z", "z": "S", "L": "L",
}


def slp1_to_hk(slp1: str) -> str:
    """Approximate SLP1->HK (Harvard-Kyoto). Standard correspondence table;
    not sanskrit-util-owned (HK is out of that package's public API)."""
    return "".join(_SLP1_TO_HK.get(ch, ch) for ch in (slp1 or ""))


def from_slp1_out(slp1: str, out: str = "iast") -> str:
    if out == "slp1":
        return slp1
    if out == "iast":
        return from_slp1(slp1)
    if out == "deva":
        return iast_to_devanagari(from_slp1(slp1))
    if out == "hk":
        return slp1_to_hk(slp1)
    raise ValueError(f"unknown output scheme: {out}")
