param(
    [string]$DifyComposeDir = "D:\newwork\lab-safe-assistant-workspace\lab-safe-assistant-github\local_env\dify\docker",
    [string]$ProjectName = "docker",
    [string]$HealthUrl = "http://127.0.0.1:8081",
    [int]$RetryCount = 30,
    [switch]$SkipNginxRefresh
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if (-not (Test-Path -LiteralPath $DifyComposeDir)) {
    throw "Dify compose directory not found: $DifyComposeDir"
}

Write-Host "[INFO] Starting Dify compose stack..."
Write-Host "[INFO] Compose dir : $DifyComposeDir"
Write-Host "[INFO] Project     : $ProjectName"
Push-Location $DifyComposeDir
try {
    docker compose -p $ProjectName up -d
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up failed with exit code $LASTEXITCODE"
    }

    if (-not $SkipNginxRefresh) {
        Write-Host "[INFO] Refreshing Dify nginx to avoid stale upstream routing..."
        docker compose -p $ProjectName restart nginx
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose restart nginx failed with exit code $LASTEXITCODE"
        }
    }

    Write-Host "[INFO] Waiting for Dify nginx on 8081..."
    $ready = $false
    for ($i = 1; $i -le $RetryCount; $i++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }

    docker compose -p $ProjectName ps

    if (-not $ready) {
        throw "Dify 8081 is not reachable after retrying: $HealthUrl"
    }

    $conn = Get-NetTCPConnection -LocalPort 8081 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $conn) {
        throw "Port 8081 has no listening process after Dify start."
    }

    Write-Host "[OK] Dify 8081 recovered: $HealthUrl"
} finally {
    Pop-Location
}
