$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeFile = Join-Path $RepoRoot "artifacts\local-dify-rag\runtime.json"
if (-not (Test-Path $RuntimeFile)) { Write-Host "[INFO] runtime file not found: $RuntimeFile"; exit 0 }
$runtime = Get-Content $RuntimeFile -Raw | ConvertFrom-Json
$proc = if ($runtime.pid) { Get-Process -Id $runtime.pid -ErrorAction SilentlyContinue } else { $null }
Write-Host "started_at : $($runtime.started_at)"
Write-Host "url        : $($runtime.url)"
Write-Host "pid        : $($runtime.pid)"
Write-Host "running    : $([bool]$proc)"
Write-Host "dify_key   : $($runtime.dify_configured)"
Write-Host "env_file   : $($runtime.env_file)"
Write-Host "log_file   : $($runtime.log_file)"
if ($runtime.demo_port) {
    try {
        $health = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$($runtime.demo_port)/health" -TimeoutSec 5
        Write-Host "health     : $($health.StatusCode) $($health.Content)"
    } catch { Write-Host "health     : unavailable ($($_.Exception.Message))" }
}
