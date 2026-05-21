$NgrokPath = "C:\Users\Windows\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
if (-not (Test-Path $NgrokPath)) {
    Write-Host "Ngrok not found in default Winget path. Searching..." -ForegroundColor Yellow
    $NgrokPath = (Get-ChildItem -Path $env:LOCALAPPDATA -Filter ngrok.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
}

if ($NgrokPath) {
    Write-Host "Starting ngrok for port 5000..." -ForegroundColor Cyan
    & $NgrokPath http 5000
} else {
    Write-Host "Error: ngrok.exe not found." -ForegroundColor Red
}
