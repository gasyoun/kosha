# One-off registration for the H3743 pwg_ru recrawl watchdog.
# schtasks.exe path used deliberately - Register-ScheduledTask is broken on
# this box (H3597 report Sec8).

$taskName = 'kosha-h3743-pwgru-recrawl-watchdog'
$repo = 'C:\Users\user\Documents\GitHub\kosha-h3743-807629'
$tick = Join-Path $repo 'scripts\pwgru_watchdog_tick.ps1'
$psExe = (Get-Command powershell).Source

$trArg = '"' + $psExe + '" -NoProfile -ExecutionPolicy Bypass -File "' + $tick + '"'

schtasks.exe /Create /TN $taskName /TR $trArg /SC MINUTE /MO 10 /RL LIMITED /F
schtasks.exe /Query /TN $taskName /V /FO LIST
