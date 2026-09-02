$ErrorActionPreference = 'Stop'
try {
    $task = Get-ScheduledTask -TaskName 'kosha-h3743-pwgru-recrawl-watchdog'
    $task.Settings.StartWhenAvailable = $true
    $task.Settings.WakeToRun = $true
    $task.Settings.DisallowStartIfOnBatteries = $false
    $task.Settings.StopIfGoingOnBatteries = $false
    Set-ScheduledTask -InputObject $task | Out-Null
    Write-Output 'Settings applied OK'
}
catch {
    $msg = $_.Exception.Message
    Write-Output "FAILED: $msg"
}
