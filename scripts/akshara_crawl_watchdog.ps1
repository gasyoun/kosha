# akshara_crawl_watchdog.ps1 - H3597 self-healing supervisor for the FULL kosha crawl.
#
# Scheduled task 'kosha-akshara-crawl-watchdog' fires this every 10 min (StartWhenAvailable
# + WakeToRun). Contract:
#   alive + manifest appended <10 min ago  -> log "healthy", exit
#   alive but stale >10 min (wedged)       -> taskkill, fall through to relaunch
#   dead                                   -> relaunch pass 1 or --ru from the resume logs
#   both passes exhausted (done+failed == total) -> log + self-disable (no orphaned task)
#
# Double-crawler safety: the process check is command-line based and re-verified immediately
# before every launch; the task itself runs IgnoreNew.
#
# Log: data/akshara_full/watchdog.log
#
# -CrawlRoot (SPOF fix 28-08-2026): the scheduled task lives on the PERSISTENT
# kosha main clone but the crawl tree it supervises may be a session worktree
# (H3597: kosha-h3597-14872). Default = the repo root this script lives in
# (original single-tree behavior).

param(
    [string]$CrawlRoot = ''
)

$ErrorActionPreference = 'Stop'
if ($CrawlRoot) {
    $root = (Resolve-Path -LiteralPath $CrawlRoot).Path
} else {
    $root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}
$dataDir = Join-Path $root 'data\akshara_full'
$log = Join-Path $dataDir 'watchdog.log'
$manifest = Join-Path $dataDir 'head_manifest.jsonl'
$log1 = Join-Path $dataDir 'crawl_manifest.jsonl'
$log2 = Join-Path $dataDir 'crawl_manifest_ru.jsonl'
$staleMin = 10

function Log($msg) {
    "$(Get-Date -Format o) $msg" | Add-Content -LiteralPath $log -Encoding utf8
}

function Get-Crawlers {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match 'akshara_full_crawl\.py' }
}

function Get-LogStats($path) {
    # (lines_with_http_200, lines_total) - cheap counting, no JSON parsing.
    if (-not (Test-Path -LiteralPath $path)) { return 0, 0 }
    $hits = (Select-String -LiteralPath $path -SimpleMatch '"http": 200').Count
    $all = (Get-Content -LiteralPath $path | Measure-Object -Line).Lines
    return $hits, $all
}

function Start-Pass([string[]]$extraArgs, [string]$outLog, [string]$errLog) {
    Start-Process -FilePath 'python' `
        -ArgumentList (@('scripts\akshara_full_crawl.py') + $extraArgs) `
        -WorkingDirectory $root -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $dataDir $outLog) `
        -RedirectStandardError (Join-Path $dataDir $errLog) | Out-Null
}

try {
    $total = (Get-Content -LiteralPath $manifest | Measure-Object -Line).Lines

    $procs = @(Get-Crawlers)
    if ($procs.Count -gt 0) {
        $fresh = $false
        foreach ($l in @($log1, $log2)) {
            if (Test-Path -LiteralPath $l) {
                $age = ((Get-Date) - (Get-Item -LiteralPath $l).LastWriteTime).TotalMinutes
                if ($age -lt $staleMin) { $fresh = $true }
            }
        }
        if ($fresh) {
            Log "healthy: crawler pid(s) $($procs.ProcessId -join ','), manifest fresh"
            exit 0
        }
        Log "WEDGED: crawler alive but no manifest write in >$staleMin min - killing pid(s) $($procs.ProcessId -join ',')"
        $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Seconds 3
    }

    # Dead (or just killed): which pass is incomplete?
    ($done1, $all1) = Get-LogStats $log1
    ($done2, $all2) = Get-LogStats $log2

    if ($done1 -lt $total) {
        if ($all1 -ge $total) {
            Log "pass1 exhausted: done=$done1 failed=$(($all1 - $done1)) of $total - leaving failed keys to the drain report; self-disabling"
            Disable-ScheduledTask -TaskName 'kosha-akshara-crawl-watchdog' | Out-Null
            exit 0
        }
        Log "restarting pass 1: done=$done1/$total"
        Start-Pass @() 'run_pass1.log' 'run_pass1.err'
        exit 0
    }

    if ($done2 -lt ($total * 3)) {
        if ($all2 -ge ($total * 3)) {
            Log "pass2 exhausted: done=$done2 failed=$(($all2 - $done2)) of $($total * 3) - leaving failed keys to the drain report; self-disabling"
            Disable-ScheduledTask -TaskName 'kosha-akshara-crawl-watchdog' | Out-Null
            exit 0
        }
        Log "restarting pass 2 (ru): done=$done2/$($total * 3)"
        Start-Pass @('--ru') 'run_pass2.log' 'run_pass2.err'
        exit 0
    }

    Log "ALL PASSES DONE: pass1=$done1 pass2=$done2 - crawl complete; self-disabling"
    Disable-ScheduledTask -TaskName 'kosha-akshara-crawl-watchdog' | Out-Null
    exit 0
}
catch {
    Log "watchdog ERROR: $($_ | Out-String)"
    exit 1
}
