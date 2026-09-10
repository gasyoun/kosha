"""P2 static-cache generator tests (scripts/build_static_cache.py).

Locks the two invariants the Pages tier depends on:
  * every generated card is byte-identical to the live /api/v1/lemma response
    (so the static tier and the dynamic API never diverge — D5-3);
  * card_token is a lossless, case-preserving, JS-reproducible encoding.

Local-only (A3): requires data/db/kosha.db built (scripts/build_db.py).
"""
import json
import sys
import tarfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from app.main import app  # noqa: E402
import build_static_cache as bsc  # noqa: E402
from kosha.settings import get_settings  # noqa: E402

client = TestClient(app)

FIXTURE_DB = ROOT / "data" / "db" / "kosha_fixture.db"


def _core_db():
    # Resolve through the typed settings, not the generator's CLI default:
    # one source of truth for where the core DB lives (KOSHA_CORE_DB_PATH
    # included), matching tests/conftest.py::_core_db_present.
    return get_settings().core_db


def _fixture_db():
    if not FIXTURE_DB.is_file():
        pytest.skip("fixture DB absent — build with "
                     "`python scripts/build_db.py --profile fixture`")
    return FIXTURE_DB


@pytest.mark.parametrize("slp1", ["ca", "iti", "BU", "agni", "indra"])
def test_card_matches_live_api(slp1):
    con = bsc.open_db(_core_db())
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
    con = bsc.open_db(_core_db())
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
    con = bsc.open_db(_core_db())
    try:
        bsc.build_index(con, tmp_path)
    finally:
        con.close()
    index = json.loads((tmp_path / "js" / "data" / "lemmas.json").read_text(encoding="utf-8"))
    assert index["fields"] == ["slp1", "iast", "dicts"]
    assert len(index["rows"]) == 323425
    att = json.loads((tmp_path / "js" / "data" / "attested_keys.json").read_text(encoding="utf-8"))
    assert att["count"] == 50355 == len(att["tokens"])


def test_full_tarball_resumes_after_a_simulated_kill(tmp_path, monkeypatch):
    """H4407: a kill mid-run must not restart the 222k-lemma_card build from
    zero. Simulates `kill -9` by raising out of `lemma_card` partway through
    — the same abrupt-stop shape a real process kill leaves behind, since the
    per-card flush() calls already made everything up to that point durable.
    """
    con = bsc.open_db(_fixture_db())
    try:
        keys = [r["slp1_key"] for r in con.execute(
            "SELECT DISTINCT slp1_key FROM entries ORDER BY slp1_key"
        ).fetchall()]
        assert len(keys) >= 3, "fixture pack needs >=3 entry-bearing lemmas for this test"

        tar_path = tmp_path / "cards_full.tar.gz"
        stage = tar_path.with_suffix(tar_path.suffix + ".stage")
        done = tar_path.with_suffix(tar_path.suffix + ".done")

        real_lemma_card = bsc.lemma_card
        calls = {"n": 0}

        def _kill_after_two(con_, slp1, dv, out="iast"):
            calls["n"] += 1
            if calls["n"] > 2:
                raise RuntimeError("simulated kill -9 mid-run")
            return real_lemma_card(con_, slp1, dv, out=out)

        monkeypatch.setattr(bsc, "lemma_card", _kill_after_two)
        with pytest.raises(RuntimeError, match="simulated kill"):
            bsc.build_full_tarball(con, tar_path)

        assert stage.is_file() and done.is_file()
        assert not tar_path.exists()
        staged_before = done.read_text(encoding="utf-8").splitlines()
        assert len(staged_before) == 2
        with tarfile.open(stage, "r") as tar:
            assert len(tar.getnames()) == 2

        # Resume: no crash this time — must pick up exactly where it left off,
        # not redo the first two cards or skip any of the rest.
        monkeypatch.setattr(bsc, "lemma_card", real_lemma_card)
        bsc.build_full_tarball(con, tar_path)

        assert tar_path.is_file()
        assert not stage.exists() and not done.exists()
        with tarfile.open(tar_path, "r:gz") as tar:
            names = tar.getnames()
        assert len(names) == len(keys) == len(set(names)), "no duplicate/missing members"
        assert set(names) == {f"cards/{bsc.card_token(k)}.json" for k in keys}
    finally:
        con.close()
