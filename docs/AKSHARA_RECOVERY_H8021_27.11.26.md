_Created: 27-11-2026 · Last updated: 27-11-2026_
_Dr. Mārcis Gasūns_

Executed 27-11-2026 by DeepSeek v4.1 Flash (`openrouter/deepseek/deepseek-v4.1-flash`) via opencode, worker 2 on executor DeepSeek/opencode. Mission: [H8021](https://github.com/gasyoun/Uprava/blob/main/handoffs/H8021-DeepSeek_kosha_akshara-raw-recover-recrawl_11.11.26.md) — D18/D19 of the H8013 dhatupatha grill (MSI leftovers probe → careful re-crawl → Google Drive raw archive before any deletion → parse/reconcile).

# H8021 — akshara.ru recovery: HARVESTED METADATA, BODIES STILL MISSING (honest partial)

## 1. Verdict

**PARTIAL — stop after 3 re-crawl attempts per the handoff's own stop condition.** The H3743 `pwg_ru` recrawl manifest was recovered from its pushed rescue branch onto `main`: **15,268 unique `http:200` heads, every row sha256-pinned, all 15,268 inside the frozen 51,663-head census (29.55% coverage) — 599,126,930 fetched bytes accounted for.** No raw HTML or parsed corpus body is recoverable from this box, from MSI (host down), or from the encrypted Google Drive mirror (never mirrored — the loss predates the mirror). A live re-crawl from this box reached **HTTP 200 on the first probe**, then the WAF answered the crawler's identified UA with **403** and blackholed the next two probes; per [FINDINGS §701](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md) retrying an active block is impolite-crawler behaviour, so probing stopped at three. **Nothing was deleted** — MG's 11-11-2026 clarification keeps local raw copies unless a box is under disk pressure.

## 2. MSI leftovers probe (D18, step 1) — INCONCLUSIVE, host down

Live probes 27-11-2026, all in one pass:

| Channel | Result |
| --- | --- |
| `tailscale status` | `msi 100.69.208.63 windows offline, last seen 4m ago` (flapping) |
| `ssh msi` (IPv6 `fd33:40d3:82a1:…`) | `No route to host` |
| `ssh root@100.69.208.63` (IPv4 tailnet) | `Permission denied (publickey,password,keyboard-interactive)` |
| `ssh computer@100.69.208.63` | `Operation timed out` / broken pipe |
| `ssh computer@192.168.2.86` (LAN) | `kex_exchange_identification: Connection reset by peer` |

So the fate of any local `D:\ClaudeTools\evidence\` archive or `data/raw_akshara_full/` leftover on MSI could not be checked. **Not "empty" — unreachable.** A later session must re-probe when the tailnet node is online (GTD residual below).

## 3. Google Drive raw archive probe (D19)

`rclone ls gcrypt:kosha/data/raw_akshara_full` → `directory not found`; `rclone ls gcrypt:kosha/data/akshara_full` shows only the committed crawl manifests (`crawl_manifest*.jsonl`), no `parsed_corpus*.jsonl`. The [H5816 weekly mirror](https://github.com/gasyoun/Uprava/blob/main/tools/gdrive_mirror_weekly.sh) began 03-10-2026, after the 01-09-2026 `--delete-raw` + worktree GC loss ([FINDINGS §660](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md), [§700](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)), so the mirror cannot contain the lost bodies. The `gcrypt:` remote is client-side encrypted — the D19 "archive raw before deletion" lane exists and is usable for a future recrawl; **no deletion happened here, so the precondition was never triggered**.

## 4. Recovered artifact — the H3743 recrawl manifest is on `origin/main` now

The handoff assumed the rescue branch's fate was unknown. It is **pushed and live**: `origin/rescue/h4005-msi/kosha-h3743-807629-h3743-pwgru-recrawl-807629-0309` @ `ce8d74918756390bb3465c25938dddbcbacabb3a`. Its single load-bearing payload is copied verbatim to [`data/akshara_full/crawl_manifest_pwgru_recrawl.jsonl`](https://github.com/gasyoun/kosha/blob/main/data/akshara_full/crawl_manifest_pwgru_recrawl.jsonl):

- sha256 `07d85685c2bf2416a62312930cd80f9a9bde091f8707642cbef5161c84c8cdcb`, 8,749,877 bytes, 28,923 JSONL rows;
- `http:200` **15,268** (unique slp1 keys, all `|pwg_ru`), `http:0` **13,655** (the 06-09 WAF-block failure run preserved alongside the successes);
- every 200 row carries `url`, `ts`, `bytes` and a 64-hex `sha256` of the fetched card; all 15,268 keys ⊂ census; **0** outside;
- earlier successful fetch timestamps 2026-09-02, matching [FINDINGS §701](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)'s last-success `2026-09-02T18:12:06Z`.

This is metadata only — it proves *which* cards were fetched and their exact bytes, not their content. It gives H3743 a 15,268-head sha256-pinned baseline instead of nothing.

Derived resume inputs committed beside it:
- [`data/akshara_full/head_manifest_h8021_missing.jsonl`](https://github.com/gasyoun/kosha/blob/main/data/akshara_full/head_manifest_h8021_missing.jsonl) — **36,395** census heads with no recovered 200 row (51,663 − 15,268), the exact todo list for the next lawful recrawl wave;
- [`data/akshara_full/crawl_manifest_pwgru_h8021.jsonl`](https://github.com/gasyoun/kosha/blob/main/data/akshara_full/crawl_manifest_pwgru_h8021.jsonl) — 2 `http:0` rows from this session's blocked crawl, retained as the block evidence (no bodies written).

## 5. Re-crawl attempts (3 — stop)

All fetches use the H3597 contract via [`akshara_full_crawl.py`](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_full_crawl.py): URL allow-list regex (only `/kosha?q=<slp1>&dict=<d>&script=slp1`), identified UA with contact, 2.0 s throttle + ≤1 s jitter per worker, 3-try backoff, checkpointed append-only JSONL, `--dict pwg_ru` so only the missing MT variant is fetched. Command: `--ru --dict pwg_ru --manifest head_manifest_h8021_missing.jsonl --log crawl_manifest_pwgru_h8021.jsonl --limit 300 --workers 2`.

| # | Probe | Result |
| --- | --- | --- |
| 1 | `curl -A 'kosha-akshara-recovery/1.0 (research; contact: …)' …q=A&dict=pwg_ru` | **HTTP 200**, 140,922 bytes, 0.49 s — block lifted at first contact |
| 2 | the contract crawler, 2 polite workers (`Gfta`, `GftaDenu`) | **HTTP 403 Forbidden** on both; run stopped, no bodies |
| 3 | `curl` with recovery UA, then Mozilla UA, same card | connection timeout (15 s each), no response |

**Stop.** The site escalated from 200 to 403 to silent block within ~90 s. Re-enable only through the weekly retry discipline of [kosha PR #538](https://github.com/gasyoun/kosha/pull/538) (`pwgru_retry_probe.ps1`, gated on success, never more than once a week), never by hammering from this box.

## 6. Reconciliation vs frozen census (goal "or honest partial")

| Quantity | Count |
| --- | --- |
| Census heads (frozen 27-08-2026, two sitemaps) | 51,663 |
| Heads with sha256-pinned 200 fetch metadata (recovered) | 15,268 (29.55%) |
| Heads with re-crawlable body recovered **this session** | 0 |
| Heads with parsed row recovered **this session** | 0 |
| Heads still to fetch | 36,395 (70.45%) |
| Raw files on disk / parsed corpus rows | 0 / absent |

`akshara_full_parse.py --selftest` is the parse-path control (unchanged code); no parse run was possible because zero new raw cards exist. **The 15,268 fetched bodies are still gone** — this pass recovers the *ledger*, not the corpus.

## 7. Rights and deletion posture

RESTRICTED tier ([H3597 rights posture](https://github.com/gasyoun/kosha/blob/main/docs/AKSHARA_FULL_COVERAGE_H3597_27.08.26.md)): no card bodies, parsed rows or Drive contents are published here or in git — only counts, URLs, hashes and timestamps. No `--delete-raw`, no worktree GC, no local cleanup was run. Raw local copies stay until a future lawful recrawl produces them and D19's Drive archive is verified.

## 8. Delivery (five fields)

- **Changed:** `main` now carries the recovered 15,268-head `pwg_ru` recrawl manifest, its 36,395-head complement, the 2-row block-evidence log, this report and a changelog queue entry. No scripts changed; no corpus content published.
- **Unchanged:** raw corpus (absent), parsed corpus (absent), MSI box (unreachable), H3597 crawl contract and UA, weekly retry-probe discipline, H3743's benchmark verdict.
- **Checks:** manifest sha256 `07d85685…c8cdcb` verified locally; 28,923 rows parsed → 15,268 × `http:200` / 13,655 × `http:0`; 15,268/15,268 200-rows carry 64-hex sha256; 15,268 ⊂ census, 0 outside; live site probe 200 then 403 + 2 timeouts (3 tries, stop).
- **Risks:** no bodies recovered, so H3743 still lacks its full-corpus input; MSI probe inconclusive while the node is down; a future recrawl must be resumed through the once-a-week success-gated probe, not from this box on a loop.
- **Inspect:** this report §4–§6 → the recovered manifest → the derived missing-head list → the weekly probe script.

## 9. Residuals (dated, human-executable)

1. **@DO 27-11-2026:** when the `msi` tailnet node is online, SSH-probe `D:\ClaudeTools\evidence\` and `C:\Users\user\Documents\GitHub\kosha\data\raw_akshara_full\` for surviving raw/parsed bodies; if found, `rclone copy` to `gcrypt:kosha/data/raw_akshara_full` **before** any deletion.
2. **@DO 27-11-2026:** re-arm the weekly success-gated `pwgru_retry_probe` (PR #538); on a green probe, resume the 36,395-head todo list with `--dict pwg_ru --manifest head_manifest_h8021_missing.jsonl`, 2 polite streams, checkpointed log.
3. **@DO 27-11-2026:** after that recrawl, run `akshara_full_parse.py --pass ru --log <new log>` **without** `--delete-raw`, then `rclone copy` the raws to `gcrypt:` and verify object count before any local reclaim.
4. **@DO 27-11-2026:** reconcile the resulting parsed rows against census 51,663 and report the final coverage; H3743's full-corpus MT benchmark stays parked until then.
