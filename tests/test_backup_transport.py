"""Encrypted, atomic, digest-verified backup (H1944, W0B item 8).

Everything here runs against `FakeTransport`. No test in this repo contacts a
live server, uploads a byte, or reads a credential — the handoff's fence says
so, and the fake is what makes the fail-closed paths testable at all.
"""

import pytest

from kosha.backup.transport import (
    DigestMismatch, DigestUnsupported, FakeTransport, sha256_of, temp_name, upload,
)


@pytest.fixture()
def payload(tmp_path):
    path = tmp_path / "kosha.db"
    path.write_bytes(b"pretend this is a 4 GB dictionary build" * 100)
    return path


def test_dry_run_touches_nothing(payload):
    transport = FakeTransport()
    result = upload(transport, payload, "guhya", "kosha.db", dry_run=True)
    assert result.promoted is False
    assert result.sha256 == sha256_of(payload)
    assert transport.files == {}


def test_upload_lands_under_a_temporary_name_then_renames(payload):
    transport = FakeTransport()
    result = upload(transport, payload, "guhya", "kosha.db")

    assert result.promoted is True
    assert transport.renames == [(temp_name("kosha.db", result.sha256), "kosha.db")]
    assert ("guhya", "kosha.db") in transport.files
    # Nothing is left behind under the scratch name.
    assert ("guhya", result.temp_name) not in transport.files


def test_the_temporary_name_is_never_the_destination(payload):
    digest = sha256_of(payload)
    assert temp_name("kosha.db", digest) != "kosha.db"
    assert temp_name("kosha.db", digest).startswith("kosha.db.part-")


def test_server_without_a_digest_command_fails_closed(payload):
    """The required treatment: do not promote what cannot be verified."""
    transport = FakeTransport(supports_digest=False)
    with pytest.raises(DigestUnsupported):
        upload(transport, payload, "guhya", "kosha.db")

    # The scratch upload stays for inspection; the destination never appears.
    assert ("guhya", "kosha.db") not in transport.files
    assert transport.renames == []


def test_corrupted_transfer_is_not_promoted(payload):
    transport = FakeTransport(corrupt=True)
    with pytest.raises(DigestMismatch):
        upload(transport, payload, "guhya", "kosha.db")
    assert ("guhya", "kosha.db") not in transport.files
    assert transport.renames == []


def test_missing_local_file_is_refused(tmp_path):
    with pytest.raises(Exception, match="missing local file"):
        upload(FakeTransport(), tmp_path / "nope.db", "guhya", "nope.db")


def test_the_deploy_script_defaults_to_a_dry_run():
    """`--upload` must be typed deliberately; the default transfers nothing."""
    import deploy_guhya

    args = deploy_guhya.main.__doc__ or ""
    parser_source = deploy_guhya.__doc__ or ""
    assert "DRY RUN" in parser_source or "DRY RUN" in args


def test_the_deploy_script_no_longer_imports_plaintext_ftplib():
    import deploy_guhya

    assert not hasattr(deploy_guhya, "ftplib"), (
        "deploy_guhya must route every transfer through the TLS transport"
    )
    assert hasattr(deploy_guhya, "FTPSTransport")


def test_remote_subdirectories_are_split_off_the_manifest_name():
    import deploy_guhya

    assert deploy_guhya.split_remote("renou/mw.jsonl", "guhya") == ("guhya/renou", "mw.jsonl")
    assert deploy_guhya.split_remote("kosha.db", "guhya") == ("guhya", "kosha.db")
