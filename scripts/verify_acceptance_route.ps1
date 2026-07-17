param(
    [string]$BaseUrl = "http://127.0.0.1:8091",
    [string]$EnvFile = "",
    [string]$DemoEnvFile = "",
    [string]$ProbeQuestion = "Please explain the difference between a laboratory SOP and SDS in one sentence.",
    [int]$ExpectedKbRows = 3000,
    [int]$ExpectedKbCategories = 50,
    [int]$KbPageLimit = 120,
    [int]$RetryCount = 3,
    [int]$RetryDelaySec = 5
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $EnvFile) {
    $EnvFile = Join-Path $RepoRoot ".env.dify_rag"
}
if (-not $DemoEnvFile) {
    $DemoEnvFile = Join-Path $RepoRoot ".env.web_demo"
}

function Read-EnvFile {
    param([string]$Path)
    $values = @{}
    foreach ($line in Get-Content -Path $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
        $pair = $trimmed -split "=", 2
        if ($pair.Count -eq 2) { $values[$pair[0].Trim()] = $pair[1].Trim().Trim([char]34) }
    }
    return $values
}

function Invoke-WithRetry {
    param(
        [scriptblock]$ScriptBlock,
        [string]$Label,
        [int]$Attempts = $RetryCount,
        [int]$DelaySec = $RetryDelaySec
    )

    $lastError = $null
    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            return & $ScriptBlock
        } catch {
            $lastError = $_
            if ($i -ge $Attempts) { break }
            Write-Host "[WARN] $Label failed on attempt $i/$Attempts, retrying in ${DelaySec}s: $($_.Exception.Message)"
            Start-Sleep -Seconds $DelaySec
        }
    }
    throw "$Label failed after $Attempts attempts: $($lastError.Exception.Message)"
}

if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Env file not found: $EnvFile"
}

$envMap = Read-EnvFile -Path $EnvFile
$demoEnvMap = if (Test-Path -LiteralPath $DemoEnvFile) { Read-EnvFile -Path $DemoEnvFile } else { @{} }
$demoPassword = [string]($demoEnvMap["DEMO_PASSWORD"])
if (-not $demoPassword) { throw "DEMO_PASSWORD is missing in $DemoEnvFile" }
$demoHeaders = @{ "x-password" = $demoPassword }
$difyBase = [string]($envMap["DIFY_BASE_URL"])
$difyKey = [string]($envMap["DIFY_APP_API_KEY"])
if (-not $difyBase) { throw "DIFY_BASE_URL is missing in $EnvFile" }
if (-not $difyKey) { throw "DIFY_APP_API_KEY is missing in $EnvFile" }
$difyApiBase = $difyBase.TrimEnd([char]47)

Write-Host "[INFO] Checking Demo health: $BaseUrl/health"
$health = Invoke-WithRetry -Label "Demo health" -ScriptBlock {
    Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 15
}
if (-not $health.ok) { throw "Demo health check returned ok=false" }
if (-not $health.dify_reachable) { throw "Demo health says Dify is not reachable: $($health.dify_error)" }
if ([int]$health.kb_loaded -lt $ExpectedKbRows) {
    throw "Expected kb_loaded >= $ExpectedKbRows, got $($health.kb_loaded)"
}

Write-Host "[INFO] Checking KB summary and paged entries..."
$kbSummary = Invoke-WithRetry -Label "KB summary" -ScriptBlock {
    Invoke-RestMethod -Uri "$BaseUrl/api/kb/summary" -Method Get -Headers $demoHeaders -TimeoutSec 20
}
if ([int]$kbSummary.total_entries -lt $ExpectedKbRows) {
    throw "Expected KB total_entries >= $ExpectedKbRows, got $($kbSummary.total_entries)"
}
if ([int]$kbSummary.total_categories -lt $ExpectedKbCategories) {
    throw "Expected KB total_categories >= $ExpectedKbCategories, got $($kbSummary.total_categories)"
}

$kbEntries = Invoke-WithRetry -Label "KB paged entries" -ScriptBlock {
    Invoke-RestMethod -Uri "$BaseUrl/api/kb/entries?limit=$KbPageLimit&offset=0" -Method Get -Headers $demoHeaders -TimeoutSec 20
}
$entryCount = @($kbEntries.entries).Count
if ([int]$kbEntries.total -lt $ExpectedKbRows) {
    throw "Expected KB entries total >= $ExpectedKbRows, got $($kbEntries.total)"
}
if ($entryCount -le 0 -or $entryCount -gt $KbPageLimit) {
    throw "Expected 1..$KbPageLimit KB entries on first page, got $entryCount"
}
if (-not $kbEntries.has_more) {
    throw "Expected KB paged entries to have has_more=true for 3000+ rows"
}

Write-Host "[INFO] Checking Dify parameters endpoint..."
$headers = @{ Authorization = "Bearer $difyKey" }
$parameters = Invoke-WithRetry -Label "Dify parameters endpoint" -ScriptBlock {
    Invoke-WebRequest -UseBasicParsing -Uri "$difyApiBase/v1/parameters" -Headers $headers -TimeoutSec 20
}
if ($parameters.StatusCode -ne 200) {
    throw "Dify parameters endpoint returned status $($parameters.StatusCode)"
}

Write-Host "[INFO] Checking Demo chat route uses dify-workflow..."
$routeQuestion = "$ProbeQuestion Route check id $([DateTime]::UtcNow.ToString("yyyyMMddHHmmss"))."
$payload = @{
    question = $routeQuestion
    mode = "lab"
    user_id = "acceptance-route"
} | ConvertTo-Json -Compress
$chat = Invoke-WithRetry -Label "Demo chat route" -ScriptBlock {
    Invoke-RestMethod -Uri "$BaseUrl/api/chat" -Method Post -Headers $demoHeaders -ContentType "application/json" -Body $payload -TimeoutSec 90
}
if ($chat.model -ne "dify-workflow") {
    throw "Expected model=dify-workflow, got model=$($chat.model), decision=$($chat.decision)"
}
if ([int]$chat.timings.upstream_ms -le 0) {
    throw "Expected a live Dify upstream call, got upstream_ms=$($chat.timings.upstream_ms)"
}

Write-Host "[OK] Acceptance route is ready"
Write-Host "Demo health : ok=$($health.ok), kb_loaded=$($health.kb_loaded), dify_reachable=$($health.dify_reachable)"
Write-Host "KB display  : total_entries=$($kbSummary.total_entries), categories=$($kbSummary.total_categories), first_page=$entryCount/$($kbEntries.limit), has_more=$($kbEntries.has_more)"
Write-Host "Dify API    : /v1/parameters 200"
Write-Host "Chat route  : model=$($chat.model), decision=$($chat.decision), citations=$($chat.citations.Count), upstream_ms=$($chat.timings.upstream_ms), elapsed_ms=$($chat.elapsed_ms)"
Write-Host "Answer len  : $(([string]$chat.answer).Length)"
