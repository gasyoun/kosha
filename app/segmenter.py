"""kosha P4 Wave K2a (H181) -- vidyut-cheda segmentation fallback.

The reverse-lookup cascade's stage 3 (app/reverse_lookup.py): when a surface
form misses BOTH the `inflections` and `forms` tables, it is very often a
sandhied / compounded string rather than a single unknown word. This module
wraps vidyut's segmenter (vidyut-cheda, D3-sanctioned per H181 -- MIT-licensed,
the same stack the Wave-E1 paradigm engine will use) to split such a string
into padas so each segment can be re-resolved through stages 1-2.

Reuse-first discipline (RISKS.md R12): vidyut runs as a LOCAL library over
VENDORED data -- neither the build nor a query ever calls a live third-party
service. The linguistic data is vendored once (a one-time `vidyut.download_data`
into `data/vidyut/`, gitignored like the other regenerable data assets) and
pointed at by KOSHA_VIDYUT_DATA. If the data is absent (a dev machine that
hasn't vendored it), segmentation degrades gracefully: `available()` is False
and the cascade reports stage 3 as unavailable instead of crashing -- exactly
how `inflections`/`forms` behave when their sibling feeds are absent.

The Chedaka is loaded lazily and memoized: the ~model load cost is paid once,
on the first form that actually falls through to segmentation, not at import.
"""
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "vidyut"

# _chedaka: None = not yet attempted; False = attempted and unavailable;
# else a live Chedaka instance.
_chedaka = None


def _data_dir() -> Path:
    return Path(os.getenv("KOSHA_VIDYUT_DATA", str(_DEFAULT_DATA)))


def _load():
    global _chedaka
    if _chedaka is not None:
        return _chedaka
    data = _data_dir()
    # cheda needs cheda/model.msgpack + kosha/ + sandhi/ under the data root.
    if not (data / "cheda" / "model.msgpack").exists():
        _chedaka = False
        return _chedaka
    try:
        from vidyut.cheda import Chedaka
        _chedaka = Chedaka(str(data))
    except Exception as e:  # noqa: BLE001 -- any load failure => unavailable, never crash a query
        print(f"[K2a] vidyut-cheda unavailable ({e!r}); segmentation fallback disabled.")
        _chedaka = False
    return _chedaka


def available() -> bool:
    return bool(_load())


def segment(slp1_text: str):
    """Split an SLP1 string into padas via vidyut-cheda.

    Returns a list of {"text": <segment SLP1>, "lemma": <SLP1 lemma or None>}.
    A single-token result (no split) or an unavailable segmenter yields a list
    that the caller can detect (empty when unavailable). Never raises.
    """
    ch = _load()
    if not ch:
        return []
    try:
        tokens = ch.run(slp1_text)
    except Exception:  # noqa: BLE001 -- a segmentation failure is a miss, not an error
        return []
    return [{"text": t.text, "lemma": t.lemma} for t in tokens]
