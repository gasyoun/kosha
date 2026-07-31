"""W0B (H1944) — the restricted-tier deploy transport.

Driven entirely against a fake FTP server. Nothing here opens a socket, and no
test can upload anything anywhere: the point is to pin the protocol the real
transport follows, not to exercise a live account.

What the fake proves, in order of how badly the old code got it wrong:

1. TLS is negotiated **before** login, and the data channel is protected. The
   previous transport was `ftplib.FTP` — credentials and the whole corpus in
   clear text.
2. Bytes land on a temporary name and are renamed into place only after the
   size matches. An interrupted 1.7 GB upload used to leave a truncated object
   sitting at the name consumers fetch.
3. A server-side hash, when the server offers one, is compared and a mismatch
   refuses the promotion.
4. When the server offers no hash, the result says so — `verified_by == "size"`
   — instead of reporting an unqualified success.
"""
from __future__ import annotations

import ftplib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import deploy_guhya  # noqa: E402
from deploy_guhya import DeployError, SecureTransport  # noqa: E402

pytestmark = pytest.mark.fixture


class FakeFTP:
    """Minimal stand-in for ftplib.FTP_TLS, recording the call sequence."""

    def __init__(self, context=None, *, hash_support=True, fail_after=None,
                 short_by=0, wrong_hash=None):
        self.context = context
        self.calls: list[str] = []
        self.files: dict[str, bytes] = {}
        self.cwd_path = "/"
        self.hash_support = hash_support
        self.fail_after = fail_after
        self.short_by = short_by
        self.wrong_hash = wrong_hash
        self.pasv = None

    # --- session ---
    def connect(self, host, port, timeout=None):
        self.calls.append(f"connect:{host}:{port}")

    def auth(self):
        self.calls.append("auth")

    def login(self, user, passwd):
        assert "auth" in self.calls, "logged in before AUTH TLS"
        self.calls.append(f"login:{user}")

    def prot_p(self):
        assert self.calls and self.calls[-1].startswith("login"), \
            "PROT P must follow login"
        self.calls.append("prot_p")

    def set_pasv(self, value):
        self.pasv = value

    def quit(self):
        self.calls.append("quit")

    def close(self):
        self.calls.append("close")

    # --- filesystem ---
    def cwd(self, path):
        if path == "/":
            self.cwd_path = "/"
        else:
            self.cwd_path = self.cwd_path.rstrip("/") + "/" + path

    def mkd(self, name):
        pass

    def _key(self, name):
        return self.cwd_path.rstrip("/") + "/" + name

    def size(self, name):
        key = self._key(name)
        if key not in self.files:
            raise ftplib.error_perm("550 not found")
        return len(self.files[key])

    def storbinary(self, cmd, fh, blocksize=8192, callback=None, rest=None):
        name = cmd.split(" ", 1)[1]
        key = self._key(name)
        buffer = bytearray(self.files.get(key, b"")[:rest] if rest else b"")
        written = 0
        while True:
            block = fh.read(blocksize)
            if not block:
                break
            if self.fail_after is not None and written + len(block) > self.fail_after:
                buffer.extend(block[:max(0, self.fail_after - written)])
                self.files[key] = bytes(buffer)
                raise ftplib.error_temp("426 connection closed")
            buffer.extend(block)
            written += len(block)
            if callback:
                callback(block)
        if self.short_by:
            buffer = buffer[:-self.short_by]
        self.files[key] = bytes(buffer)
        self.calls.append(f"stor:{name}")

    def rename(self, old, new):
        self.files[self._key(new)] = self.files.pop(self._key(old))
        self.calls.append(f"rename:{old}->{new}")

    def delete(self, name):
        key = self._key(name)
        if key not in self.files:
            raise ftplib.error_perm("550 not found")
        del self.files[key]

    def sendcmd(self, command):
        verb, _, name = command.partition(" ")
        if verb == "OPTS":
            return "200 OPTS HASH SHA-256"
        if not self.hash_support:
            raise ftplib.error_perm("500 unknown command")
        key = self._key(name)
        if key not in self.files:
            raise ftplib.error_perm("550 not found")
        if self.wrong_hash:
            return f"213 SHA-256 0-0 {self.wrong_hash} {name}"
        import hashlib
        digest = hashlib.sha256(self.files[key]).hexdigest()
        return f"213 SHA-256 0-{len(self.files[key])} {digest} {name}"


@pytest.fixture()
def payload(tmp_path):
    path = tmp_path / "corpus.jsonl"
    path.write_bytes(b"x" * (3 * 1024 * 1024 + 17))
    return path


def transport_with(fake, **kwargs):
    return SecureTransport("example.invalid", "u", "p",
                           connection_factory=lambda context=None: fake,
                           token="testtoken", **kwargs)


# --- 1. encryption ------------------------------------------------------------

def test_tls_is_negotiated_before_login_and_on_the_data_channel(payload):
    fake = FakeFTP()
    with transport_with(fake):
        pass
    assert fake.calls[:4] == ["connect:example.invalid:21", "auth", "login:u", "prot_p"]
    assert fake.pasv is True


def test_there_is_no_plaintext_transport_left():
    source = Path(deploy_guhya.__file__).read_text(encoding="utf-8")
    assert "ftplib.FTP_TLS" in source
    # `ftplib.FTP(` — the plaintext constructor — must not be reachable.
    assert "ftplib.FTP(" not in source


# --- 2. temporary name + atomic rename ---------------------------------------

def test_upload_lands_on_a_temp_name_then_renames(payload):
    fake = FakeFTP()
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        record = transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    assert record["action"] == "uploaded"
    stor = [c for c in fake.calls if c.startswith("stor:")]
    assert stor == ["stor:corpus.jsonl.uploading-testtoken"]
    assert any(c.startswith("rename:corpus.jsonl.uploading-testtoken->corpus.jsonl")
               for c in fake.calls)
    assert "/guhya/corpus.jsonl" in fake.files
    assert len(fake.files["/guhya/corpus.jsonl"]) == payload.stat().st_size


def test_rename_happens_after_the_store_not_before(payload):
    fake = FakeFTP()
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    order = [c for c in fake.calls if c.startswith(("stor:", "rename:"))]
    assert order[0].startswith("stor:")
    assert order[1].startswith("rename:")


def test_interrupted_upload_leaves_the_final_name_untouched(payload):
    fake = FakeFTP(fail_after=1024 * 1024)
    fake.files["/guhya/corpus.jsonl"] = b"previous good copy"
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        with pytest.raises(DeployError) as exc:
            transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    assert "untouched" in str(exc.value)
    assert fake.files["/guhya/corpus.jsonl"] == b"previous good copy"
    assert "/guhya/corpus.jsonl.uploading-testtoken" in fake.files


def test_resume_targets_the_temp_object_only(payload):
    fake = FakeFTP()
    size = payload.stat().st_size
    fake.files["/guhya/corpus.jsonl.uploading-testtoken"] = b"x" * (size // 2)
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        record = transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    assert record["action"] == "resumed"
    assert len(fake.files["/guhya/corpus.jsonl"]) == size


def test_short_upload_is_refused_before_promotion(payload):
    fake = FakeFTP(short_by=64)
    fake.files["/guhya/corpus.jsonl"] = b"previous good copy"
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        with pytest.raises(DeployError) as exc:
            transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    assert "short object" in str(exc.value)
    assert fake.files["/guhya/corpus.jsonl"] == b"previous good copy"


# --- 3./4. digest verification ------------------------------------------------

def test_server_hash_is_compared_and_reported(payload):
    fake = FakeFTP(hash_support=True)
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        record = transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    assert record["verified_by"] == "remote-sha256"
    assert record["remote_sha256"] == digest


def test_hash_mismatch_refuses_to_promote(payload):
    fake = FakeFTP(wrong_hash="f" * 64)
    fake.files["/guhya/corpus.jsonl"] = b"previous good copy"
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        with pytest.raises(DeployError) as exc:
            transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    assert "does not match" in str(exc.value)
    assert fake.files["/guhya/corpus.jsonl"] == b"previous good copy"


def test_server_without_hash_support_says_so(payload):
    fake = FakeFTP(hash_support=False)
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        record = transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    assert record["verified_by"] == "size"
    assert record["remote_sha256"] is None


def test_identical_remote_object_is_skipped(payload):
    fake = FakeFTP()
    fake.files["/guhya/corpus.jsonl"] = payload.read_bytes()
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        record = transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    assert record["action"] == "skipped"
    assert not [c for c in fake.calls if c.startswith("stor:")]


def test_same_size_but_different_content_is_re_uploaded(payload):
    fake = FakeFTP()
    fake.files["/guhya/corpus.jsonl"] = b"y" * payload.stat().st_size
    digest = deploy_guhya.sha256_of(payload)
    with transport_with(fake) as transport:
        record = transport.upload_atomic(payload, "guhya", "corpus.jsonl", digest)
    assert record["action"] == "uploaded"
    assert fake.files["/guhya/corpus.jsonl"] == payload.read_bytes()


# --- no upload from the CLI's read-only modes ---------------------------------

@pytest.mark.parametrize("flag", ["--dry-run", "--verify-only"])
def test_readonly_modes_never_connect(tmp_path, monkeypatch, capsys, flag):
    def explode(*a, **k):
        raise AssertionError("a read-only mode opened a connection")

    monkeypatch.setattr(deploy_guhya, "SecureTransport", explode)
    monkeypatch.setattr(deploy_guhya, "MANIFEST", [])
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"hello")
    rc = deploy_guhya.main([flag, "--file", str(sample), "--remote-name", "sample.bin"])
    assert rc == 0
    assert "No connection attempted" in capsys.readouterr().out


def test_upload_tokens_differ_between_runs():
    assert deploy_guhya.upload_token() != deploy_guhya.upload_token()
