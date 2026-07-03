"""P2 static-cache generator tests (scripts/build_static_cache.py).

Locks the two invariants the Pages tier depends on:
  * every generated card is byte-identical to the live /api/v1/lemma response
    (so the static tier and the dynamic API never diverge — D5-3);
  * card_token is a lossless, case-preserving, JS-reproducible encoding.

Local-only (A3): requires data/db/kosha.db built (scripts/build_db.py).
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from app.main import app  # noqa: E402
import build_static_cache as bsc  # noqa: E402

client = TestClient(app)


@pytest.mark.parametrize("slp1", ["ca", "iti", "BU", "agni", "indra"])
def test_card_matches_live_api(slp1):
    con = bsc.open_db(bsc.DEFAULT_DB)
    try:
        card = bsc.lemma_card(con, slp1, bsc.data_version(con))
    finally:
        con.close()
    api = client.get(f"/api/v1/lemma/{slp1}", params={"in": "slp1"}).json()
    assert card == api


def test_card_token_roundtrip_and_case():
    # Case-significant SLP1 keys must never collide on a case-insensitive FS.
    assert bsc.card_token("ka") != bsc.card_token("Ka")
    assert bsc.card_token("BU") == "_42_55"          # bhū — uppercase escaped
    assert bsc.card_token("kf") == "kf"              # lowercase kept verbatim
    # '_' itself is escaped so the encoding is unambiguous.
    assert bsc.card_token("a_b") == "a_5fb"

    def decode(tok):
        out, j = "", 0
        while j < len(tok):
            if tok[j] == "_":
                out += chr(int(tok[j + 1:j + 3], 16)); j += 3
            else:
                out += tok[j]; j += 1
        return out

    for key in ["ka", "Ka", "BU", "kf", "a_b", "ASasana", "42/55"]:
        assert decode(bsc.card_token(key)) == key


def test_generator_writes_ranked_shards(tmp_path):
    con = bsc.open_db(bsc.DEFAULT_DB)
    try:
        total = bsc.build_cards(con, tmp_path, limit=10)
    finally:
        con.close()
    assert total == 10
    files = list((tmp_path / "cards").glob("*.json"))
    assert len(files) == 10
    # each shard is a valid, self-contained lemma envelope
    sample = json.loads(files[0].read_text(encoding="utf-8"))
    assert set(sample) == {"data_version", "query", "results"}
    assert sample["results"]


def test_index_has_all_headwords(tmp_path):
    con = bsc.open_db(bsc.DEFAULT_DB)
    try:
        bsc.build_index(con, tmp_path)
    finally:
        con.close()
    index = json.loads((tmp_path / "js" / "data" / "lemmas.json").read_text(encoding="utf-8"))
    assert index["fields"] == ["slp1", "iast", "dicts"]
    assert len(index["rows"]) == 323425
    att = json.loads((tmp_path / "js" / "data" / "attested_keys.json").read_text(encoding="utf-8"))
    assert att["count"] == 50355 == len(att["tokens"])
