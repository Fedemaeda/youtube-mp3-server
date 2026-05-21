try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5
    $publicUrl = $resp.tunnels | Where-Object { $_.public_url -like "https://*" } | Select-Object -First 1 -ExpandProperty public_url

    if ($publicUrl) {
        Write-Host "Public ngrok URL:" -ForegroundColor Cyan
        Write-Host $publicUrl -ForegroundColor Green
    } else {
        Write-Host "No public HTTPS ngrok tunnel found." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not read ngrok API at http://127.0.0.1:4040." -ForegroundColor Red
    Write-Host "Make sure ngrok is running first with .\\start_ngrok.ps1" -ForegroundColor Yellow
}
