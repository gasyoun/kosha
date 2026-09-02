$repo = "C:\Users\user\Documents\GitHub\kosha-h3743-807629"
$log = Join-Path $repo "data\akshara_full\run_pwgru_recrawl.log"
$err = Join-Path $repo "data\akshara_full\run_pwgru_recrawl.err"
$pyCmd = Get-Command python
$argList = @("scripts\akshara_full_crawl.py","--ru","--dict","pwg_ru","--log","data/akshara_full/crawl_manifest_pwgru_recrawl.jsonl","--workers","2")
$proc = Start-Process -FilePath $pyCmd.Source -ArgumentList $argList -WorkingDirectory $repo -RedirectStandardOutput $log -RedirectStandardError $err -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 3
$pidVal = $proc.Id
Write-Output "PID=$pidVal"
Get-Content $log -Tail 5
