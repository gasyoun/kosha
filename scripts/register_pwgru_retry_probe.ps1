# One-off registration for the H3743 pwg_ru recrawl retry-probe task
# (weekly, starting 2026-09-13 per MG ruling "retry in 1 week" on 2026-09-06).
$taskName = 'kosha-h3743-pwgru-retry-probe'
$script = 'C:\Users\user\Documents\GitHub\kosha-h3743-retryprobe-274549\scripts\pwgru_retry_probe.ps1'
$psCmd = Get-Command powershell
$psExe = $psCmd.Source
$trArg = '"' + $psExe + '" -NoProfile -ExecutionPolicy Bypass -File "' + $script + '"'
Write-Host "TR length:" $trArg.Length
schtasks.exe /Create /TN $taskName /TR $trArg /SC WEEKLY /D MON /ST 09:00 /SD 13.09.2026 /RL LIMITED /F
schtasks.exe /Query /TN $taskName /V /FO LIST
