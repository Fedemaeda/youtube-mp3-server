$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Port = 5005

Write-Host "Starting local ZenRip server for YouTube on http://127.0.0.1:$Port" -ForegroundColor Cyan
Write-Host "Keep this window open while using the extension." -ForegroundColor Yellow

Set-Location $ProjectDir
$env:PORT = "$Port"
$env:FLASK_ENV = "development"
python app.py
