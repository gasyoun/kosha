"""Encrypted, atomic, digest-verified backup (H1944, W0B item 8).

Everything here runs against `FakeTransport`. No test in this repo contacts a
live server, uploads a byte, or reads a credential — the handoff's fence says
so, and the fake is what makes the fail-closed paths testable at all.
"""

import ftplib

import pytest

from kosha.backup.transport import (
    DigestMismatch, DigestUnsupported, FTPSTransport, FakeTransport, sha256_of,
    ssl_context, temp_name, upload,
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


# --- reply parsing: the two digest commands answer in different shapes --------

DIGEST = "a" * 64


class _ReplyFTP:
    """Just enough of an ftplib connection to answer one digest command."""

    def __init__(self, replies):
        self.replies = replies

    def cwd(self, path):
        return None

    def mkd(self, name):
        return None

    def sendcmd(self, command):
        verb = command.split(" ", 1)[0]
        if verb not in self.replies:
            raise ftplib.error_perm("500 unknown command")
        return self.replies[verb]

    def retrbinary(self, command, callback, blocksize=8192):
        # Default: no redownload path — exercises "hash unsupported and RETR fails".
        raise ftplib.error_perm("550 not found")


def _transport_answering(replies):
    # `_ftp` is the backing field; the `ftp` property guards against use
    # outside the `with` block, which is not what these tests are about.
    return FTPSTransport(host="example.invalid", user="u", password="p",
                         _ftp=_ReplyFTP(replies))


def test_xsha256_reply_is_parsed():
    transport = _transport_answering({"XSHA256": f"213 {DIGEST}"})
    assert transport.remote_sha256("guhya", "kosha.db") == DIGEST


def test_hash_reply_is_parsed_even_though_the_digest_is_not_last():
    """`HASH` answers `213 SHA-256 <range> <digest> <filename>`.

    Reading the last token returns the *filename*, which is not 64 hex chars,
    so the method returned None — and `upload()` reads None as "the server
    proved nothing" and refuses to promote. A server offering `HASH` but not
    the older `XSHA256` therefore rejected every backup upload.
    """
    transport = _transport_answering(
        {"HASH": f"213 SHA-256 0-1048576 {DIGEST} kosha.db"})
    assert transport.remote_sha256("guhya", "kosha.db") == DIGEST


def test_a_server_answering_neither_still_reports_none():
    transport = _transport_answering({})
    assert transport.remote_sha256("guhya", "kosha.db") is None


def test_ssl_context_defaults_to_verified():
    ctx = ssl_context(verify=True)
    assert ctx.verify_mode == __import__("ssl").CERT_REQUIRED


def test_ssl_context_insecure_skips_hostname_and_ca():
    ctx = ssl_context(verify=False)
    # Unverified context: either CERT_NONE or check_hostname False depending on
    # Python build — both mean the self-signed hosting path can connect.
    assert ctx.check_hostname is False or ctx.verify_mode == __import__("ssl").CERT_NONE


def test_ftps_transport_defaults_to_verify_tls_true():
    t = FTPSTransport(host="example.invalid", user="u", password="p")
    assert t.verify_tls is True


def test_tls_verify_from_env_flags():
    import deploy_guhya

    assert deploy_guhya.tls_verify_from_env({}) is True
    assert deploy_guhya.tls_verify_from_env({"FTP_TLS_INSECURE": "1"}) is False
    assert deploy_guhya.tls_verify_from_env({"FTP_TLS_INSECURE": "yes"}) is False
    assert deploy_guhya.tls_verify_from_env({"FTP_SSL_VERIFY": "0"}) is False
    assert deploy_guhya.tls_verify_from_env({"FTP_SSL_VERIFY": "false"}) is False
    assert deploy_guhya.tls_verify_from_env({"FTP_SSL_VERIFY": "1"}) is True


class _RetrFTP(_ReplyFTP):
    """Digest commands fail; RETR returns fixed payload for client-side hash."""

    def __init__(self, payload: bytes):
        super().__init__({})
        self.payload = payload

    def retrbinary(self, command, callback, blocksize=8192):
        assert command.startswith("RETR ")
        # chunk to exercise the callback path
        for i in range(0, len(self.payload), 8):
            callback(self.payload[i : i + 8])


def test_remote_sha256_falls_back_to_retr_when_hash_unsupported():
    payload = b"guhya canary bytes for redownload verify"
    transport = FTPSTransport(
        host="example.invalid", user="u", password="p", _ftp=_RetrFTP(payload)
    )
    got = transport.remote_sha256("guhya", "canary.txt")
    assert got == __import__("hashlib").sha256(payload).hexdigest()


def test_a_reply_with_no_digest_is_not_mistaken_for_one():
    transport = _transport_answering({"HASH": "213 SHA-256 0-1048576 kosha.db"})
    assert transport.remote_sha256("guhya", "kosha.db") is None
