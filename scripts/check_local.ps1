$urls = @(
  "http://localhost:8080/health",
  "http://localhost:8080/health/services",
  "http://localhost:8090/login",
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
  try {
    $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 10
    Write-Host "OK  $u  $($r.StatusCode)" -ForegroundColor Green
  } catch {
    Write-Host "ERR $u  $($_.Exception.Message)" -ForegroundColor Red
  }
}
