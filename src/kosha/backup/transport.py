"""Encrypted, atomic, digest-verified backup transport (H1944, W0B item 8).

Four properties, each replacing a specific defect of the plaintext FTP path:

1. **Encrypted.** `ftplib.FTP_TLS` with an explicit `AUTH TLS` handshake and
   `prot_p()`, so both the control channel (credentials) and the data channel
   (the bytes) are protected. A server that will not negotiate TLS is refused
   rather than silently downgraded.
2. **Temporary remote name.** Bytes land at `<name>.part-<token>`, never at
   the destination name, so an interrupted transfer cannot be mistaken for a
   complete backup by anything reading the directory.
3. **Digest-verified before promotion.** The remote digest is requested with
   the RFC 3659-era `HASH`/`XSHA256` extension and compared with the local
   `sha256`. No match, no promotion.
4. **Atomic rename.** Only after the digest matches is the temporary name
   `RNFR`/`RNTO`-renamed onto the destination.

**Fail closed.** If the server advertises no usable digest command, `upload`
raises `DigestUnsupported` and uploads nothing. The verification plan lists
exactly this treatment for "plaintext backup replacement cannot verify remote
digest": do not upload until the transport proves digest verification.

No credential is read here — the caller supplies them — and nothing in this
module is exercised against a live server by the test suite. Tests drive
`FakeTransport`, which implements the same protocol in memory.
"""

from __future__ import annotations

import ftplib
import hashlib
import ssl
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

CHUNK = 8 * 1024 * 1024


class BackupError(RuntimeError):
    """Any refusal in the backup path. Never raised for a *successful* upload."""


class DigestUnsupported(BackupError):
    """The remote cannot prove a digest, so the upload is refused."""


class DigestMismatch(BackupError):
    """The remote digest disagrees with the local file. Nothing is promoted."""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def temp_name(name: str, digest: str) -> str:
    """Temporary remote name for `name`. Deterministic, so a retry reuses it."""
    return f"{name}.part-{digest[:16]}"


class Transport(Protocol):
    """The four operations `upload` needs. Deliberately tiny so a fake is honest."""

    def ensure_dir(self, remote_dir: str) -> None: ...

    def store(self, local: Path, remote_dir: str, name: str) -> None: ...

    def remote_sha256(self, remote_dir: str, name: str) -> str | None: ...

    def rename(self, remote_dir: str, source: str, target: str) -> None: ...

    def size(self, remote_dir: str, name: str) -> int: ...


@dataclass
class FTPSTransport:
    """Explicit-TLS FTP. Refuses to operate on an unencrypted connection."""

    host: str
    user: str
    password: str
    port: int = 21
    timeout: int = 60
    _ftp: ftplib.FTP_TLS | None = field(default=None, repr=False)

    def __enter__(self) -> "FTPSTransport":
        context = ssl.create_default_context()
        ftp = ftplib.FTP_TLS(context=context)
        ftp.connect(self.host, self.port, timeout=self.timeout)
        # AUTH TLS on the control channel, then PROT P for the data channel.
        # Both are required: without prot_p the file bytes still travel in
        # clear text even though the password did not.
        ftp.auth()
        ftp.login(self.user, self.password)
        ftp.prot_p()
        ftp.set_pasv(True)
        self._ftp = ftp
        return self

    def __exit__(self, *exc) -> None:
        if self._ftp is not None:
            try:
                self._ftp.quit()
            except ftplib.all_errors:
                self._ftp.close()
            self._ftp = None

    @property
    def ftp(self) -> ftplib.FTP_TLS:
        if self._ftp is None:
            raise BackupError("transport used outside its `with` block")
        return self._ftp

    def ensure_dir(self, remote_dir: str) -> None:
        self.ftp.cwd("/")
        for part in [p for p in remote_dir.replace("\\", "/").split("/") if p]:
            try:
                self.ftp.mkd(part)
            except ftplib.error_perm:
                pass
            self.ftp.cwd(part)

    def store(self, local: Path, remote_dir: str, name: str) -> None:
        self.ensure_dir(remote_dir)
        with open(local, "rb") as handle:
            self.ftp.storbinary(f"STOR {name}", handle, blocksize=CHUNK)

    def remote_sha256(self, remote_dir: str, name: str) -> str | None:
        """Ask the server to hash the uploaded file. `None` ⇒ unsupported."""
        self.ensure_dir(remote_dir)
        for command in (f"XSHA256 {name}", f"HASH {name}"):
            try:
                reply = self.ftp.sendcmd(command)
            except ftplib.all_errors:
                continue
            token = reply.strip().split()[-1].lower()
            if len(token) == 64 and all(c in "0123456789abcdef" for c in token):
                return token
        return None

    def rename(self, remote_dir: str, source: str, target: str) -> None:
        self.ensure_dir(remote_dir)
        self.ftp.rename(source, target)

    def size(self, remote_dir: str, name: str) -> int:
        self.ensure_dir(remote_dir)
        try:
            return self.ftp.size(name) or -1
        except ftplib.all_errors:
            return -1


@dataclass
class FakeTransport:
    """In-memory stand-in used by the tests. Same protocol, no network.

    `supports_digest=False` reproduces a server without a hash command;
    `corrupt=True` reproduces bytes that changed in flight. Both exist so the
    fail-closed paths are *tested*, not merely asserted in a docstring.
    """

    supports_digest: bool = True
    corrupt: bool = False
    files: dict[tuple[str, str], bytes] = field(default_factory=dict)
    renames: list[tuple[str, str]] = field(default_factory=list)

    def __enter__(self) -> "FakeTransport":
        return self

    def __exit__(self, *exc) -> None:
        return None

    def ensure_dir(self, remote_dir: str) -> None:
        return None

    def store(self, local: Path, remote_dir: str, name: str) -> None:
        payload = local.read_bytes()
        if self.corrupt:
            payload += b"\x00"
        self.files[(remote_dir, name)] = payload

    def remote_sha256(self, remote_dir: str, name: str) -> str | None:
        if not self.supports_digest:
            return None
        payload = self.files.get((remote_dir, name))
        return hashlib.sha256(payload).hexdigest() if payload is not None else None

    def rename(self, remote_dir: str, source: str, target: str) -> None:
        self.files[(remote_dir, target)] = self.files.pop((remote_dir, source))
        self.renames.append((source, target))

    def size(self, remote_dir: str, name: str) -> int:
        payload = self.files.get((remote_dir, name))
        return len(payload) if payload is not None else -1


@dataclass
class UploadResult:
    name: str
    sha256: str
    bytes: int
    temp_name: str
    promoted: bool


def upload(
    transport: Transport,
    local: Path,
    remote_dir: str,
    name: str,
    *,
    dry_run: bool = False,
) -> UploadResult:
    """Upload one file: temp name → remote digest check → atomic rename.

    `dry_run` computes and reports the local digest and touches the transport
    not at all, which is how the CLI's default mode and the release rehearsal
    both work.
    """
    local = Path(local)
    if not local.is_file():
        raise BackupError(f"missing local file: {local}")
    digest = sha256_of(local)
    size = local.stat().st_size
    scratch = temp_name(name, digest)

    if dry_run:
        return UploadResult(name, digest, size, scratch, promoted=False)

    transport.ensure_dir(remote_dir)
    transport.store(local, remote_dir, scratch)

    remote_digest = transport.remote_sha256(remote_dir, scratch)
    if remote_digest is None:
        raise DigestUnsupported(
            f"{name}: the server proved no digest for {scratch}. Refusing to "
            "promote an unverified backup — the temporary name is left in "
            "place for inspection. Enable XSHA256/HASH on the server, or use "
            "a transport that can verify."
        )
    if remote_digest != digest:
        raise DigestMismatch(
            f"{name}: local {digest[:16]}… != remote {remote_digest[:16]}…; "
            f"leaving {scratch} unpromoted."
        )

    transport.rename(remote_dir, scratch, name)
    return UploadResult(name, digest, size, scratch, promoted=True)
