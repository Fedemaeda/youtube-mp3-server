$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting local ZenRip server and public ngrok tunnel..." -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$ProjectDir\start_local_youtube_server.ps1`""
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$ProjectDir\start_ngrok.ps1`""

Write-Host "Waiting for ngrok to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

& "$ProjectDir\get_ngrok_url.ps1"

Write-Host ""
Write-Host "Use that URL in the extension as 'YouTube Server URL'." -ForegroundColor Green
