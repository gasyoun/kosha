# H3743 pwg_ru recrawl retry probe (FINDINGS Sec701).
#
# akshara.ru TLS-blocked this box's IP on ~2026-09-02; MG ruled "retry in 1
# week" (2026-09-06). This weekly probe checks whether the block has lifted
# by fetching one real card page. On success it re-enables the recrawl
# watchdog task (kosha-h3743-pwgru-recrawl-watchdog), which then relaunches
# the crawler on its own next 10-min tick - self-disabling here so it never
# runs again once the handoff is unblocked. On failure it logs and waits for
# next week's run; NEVER retries more often than weekly (impolite-crawler
# avoidance - the whole point of this probe is not to hammer a blocking host).

$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\user\Documents\GitHub\kosha-h3743-807629'
$dataDir = Join-Path $repo 'data\akshara_full'
$logFile = Join-Path $dataDir 'pwgru_retry_probe.log'
$watchdogTask = 'kosha-h3743-pwgru-recrawl-watchdog'
$probeTask = 'kosha-h3743-pwgru-retry-probe'
$probeUrl = 'https://akshara.ru/kosha?q=A&dict=pwg_ru&script=slp1'

function Log($msg) {
    "$(Get-Date -Format o) $msg" | Add-Content -LiteralPath $logFile -Encoding utf8
}

try {
    if (-not (Test-Path -LiteralPath $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    }

    try {
        $resp = Invoke-WebRequest -Uri $probeUrl -UseBasicParsing -TimeoutSec 15 -Headers @{ 'User-Agent' = 'kosha-akshara-bench/1.0 (contact: MG, benchmark-only)' }
        $ok = ($resp.StatusCode -eq 200)
    }
    catch {
        $ok = $false
        Log "probe FAILED: $($_.Exception.Message)"
    }

    if ($ok) {
        Log "probe SUCCEEDED (http 200) - block appears lifted, re-enabling $watchdogTask"
        schtasks.exe /Change /TN $watchdogTask /ENABLE | Out-Null
        Log "re-enabled $watchdogTask; self-disabling $probeTask (its job is done)"
        schtasks.exe /Change /TN $probeTask /DISABLE | Out-Null
        exit 0
    }
    else {
        Log "still blocked - leaving $watchdogTask disabled, $probeTask will retry next week"
        exit 0
    }
}
catch {
    Log "probe script ERROR: $($_ | Out-String)"
    exit 1
}
