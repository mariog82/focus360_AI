$urls = @(
  "http://localhost:8080/health",
  "http://localhost:8080/health/services",
  "http://localhost:8001/health",
  "http://localhost:8002/health",
  "http://localhost:8003/health",
  "http://localhost:8004/health",
  "http://localhost:8005/health",
  "http://localhost:8006/health",
  "http://localhost:8007/health",
  "http://localhost:8008/health",
  "http://localhost:8009/health"
)
foreach ($u in $urls) {
  Write-Host "\n== $u ==" -ForegroundColor Cyan
  try { Invoke-RestMethod -Uri $u -TimeoutSec 5 | ConvertTo-Json -Depth 6 }
  catch { Write-Host "ERRORE: $($_.Exception.Message)" -ForegroundColor Red }
}
