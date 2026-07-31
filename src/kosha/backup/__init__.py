"""kosha backup transport (W0B item 8, H1944).

The restricted-tier backup used to speak plaintext FTP: credentials and ~2 GB
of corpus bytes crossed the wire unencrypted, an interrupted transfer left a
truncated file under the *final* name, and nothing checked that what landed on
the server matched what left this machine.

[`transport`](https://github.com/gasyoun/kosha/blob/main/src/kosha/backup/transport.py)
replaces all three: TLS-encrypted control *and* data channels, upload to a
temporary remote name with an atomic rename into place, and a mandatory remote
digest check before that rename. When the server cannot prove the digest, the
upload fails closed — the treatment the verification plan requires.
"""
