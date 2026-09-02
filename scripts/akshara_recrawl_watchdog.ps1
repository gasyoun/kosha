# akshara_recrawl_watchdog.ps1 - H3743 self-healing supervisor for a single-dict
# akshara.ru MT recrawl (e.g. the pwg_ru corpus lost to a premature worktree GC,
# FINDINGS Sec660). Generalizes akshara_crawl_watchdog.ps1 (H3597, hardcoded to
# the dict=all + dict=mw_ru|apte_ru|pwg_ru two-pass shape) to an arbitrary single
# --dict / --log recrawl so it isn't tied to that pass structure.
#
# Scheduled task fires this every 10 min (StartWhenAvailable + WakeToRun). Contract:
#   alive + manifest appended <10 min ago  -> log "healthy", exit
#   alive but stale >10 min (wedged)       -> taskkill (THIS crawl's pid only, matched
#                                              on the --log arg so a sibling akshara
#                                              crawler in another worktree is untouched),
#                                              fall through to relaunch
#   dead                                   -> relaunch from the resume log
#   manifest rows >= Total                 -> log + self-disable (no orphaned task)
#
# Log: <CrawlRoot>/data/akshara_full/<LogFile>.watchdog.log

param(
    [Parameter(Mandatory = $true)][string]$CrawlRoot,
    [Parameter(Mandatory = $true)][string]$LogFile,      # filename only, under data/akshara_full, e.g. crawl_manifest_pwgru_recrawl.jsonl
    [Parameter(Mandatory = $true)][string]$Dict,         # mw_ru | apte_ru | pwg_ru
    [int]$Workers = 2,
    [Parameter(Mandatory = $true)][int]$Total,           # expected row count at completion (census heads x 1 dict)
    [Parameter(Mandatory = $true)][string]$TaskName
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $CrawlRoot).Path
$dataDir = Join-Path $root 'data\akshara_full'
$crawlLog = Join-Path $dataDir $LogFile
$watchdogLog = Join-Path $dataDir ($LogFile + '.watchdog.log')
$staleMin = 10
$ExtraArgs = @('--ru', '--dict', $Dict, '--log', ('data/akshara_full/' + $LogFile), '--workers', $Workers)

function Log($msg) {
    "$(Get-Date -Format o) $msg" | Add-Content -LiteralPath $watchdogLog -Encoding utf8
}

function Get-Crawlers {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match [regex]::Escape($LogFile) }
}

function Get-LogStats {
    if (-not (Test-Path -LiteralPath $crawlLog)) { return 0, 0 }
    $hits = (Select-String -LiteralPath $crawlLog -SimpleMatch '"http": 200').Count
    $all = (Get-Content -LiteralPath $crawlLog | Measure-Object -Line).Lines
    return $hits, $all
}

function Start-Crawl {
    $outLog = Join-Path $dataDir ($LogFile + '.stdout.log')
    $errLog = Join-Path $dataDir ($LogFile + '.stderr.log')
    Start-Process -FilePath 'python' `
        -ArgumentList (@('scripts\akshara_full_crawl.py') + $ExtraArgs) `
        -WorkingDirectory $root -WindowStyle Hidden `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog | Out-Null
}

try {
    $procs = @(Get-Crawlers)
    if ($procs.Count -gt 0) {
        $fresh = $false
        if (Test-Path -LiteralPath $crawlLog) {
            $age = ((Get-Date) - (Get-Item -LiteralPath $crawlLog).LastWriteTime).TotalMinutes
            if ($age -lt $staleMin) { $fresh = $true }
        }
        if ($fresh) {
            Log "healthy: crawler pid(s) $($procs.ProcessId -join ','), manifest fresh"
            exit 0
        }
        Log "WEDGED: crawler alive but no manifest write in >$staleMin min - killing pid(s) $($procs.ProcessId -join ',')"
        $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Seconds 3
    }

    ($done, $all) = Get-LogStats

    if ($done -ge $Total) {
        Log "DONE: done=$done of $Total - recrawl complete; self-disabling"
        Disable-ScheduledTask -TaskName $TaskName | Out-Null
        exit 0
    }
    if ($all -ge $Total -and $done -lt $Total) {
        Log "EXHAUSTED with gaps: done=$done failed=$($all - $done) of $Total - leaving failed keys to the parse/repair step; self-disabling"
        Disable-ScheduledTask -TaskName $TaskName | Out-Null
        exit 0
    }

    Log "restarting: done=$done/$Total"
    Start-Crawl
    exit 0
}
catch {
    Log "watchdog ERROR: $($_ | Out-String)"
    exit 1
}
