# Thin wrapper so the scheduled task's /TR string stays under schtasks' 261-char
# cap - all real params are baked in here, not on the schtasks command line.
& "C:\Users\user\Documents\GitHub\kosha-h3743-807629\scripts\akshara_recrawl_watchdog.ps1" `
    -CrawlRoot "C:\Users\user\Documents\GitHub\kosha-h3743-807629" `
    -LogFile "crawl_manifest_pwgru_recrawl.jsonl" `
    -Dict pwg_ru -Workers 2 -Total 51663 `
    -TaskName "kosha-h3743-pwgru-recrawl-watchdog"
