param(
    [string]$BaseUrl = "http://127.0.0.1:8091",
    [string]$OutputDir = "",
    [string]$ReportLabel = "",
    [switch]$SkipDifyRecover,
    [switch]$SkipBackup
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RepoRoot = Split-Path -Parent $PSScriptRoot
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (-not $ReportLabel) {
    $ReportLabel = "acceptance_$stamp"
}
if (-not $OutputDir) {
    $OutputDir = Join-Path $RepoRoot "artifacts\acceptance_precheck\$stamp"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$logFile = Join-Path $OutputDir "precheck.log"
$summaryFile = Join-Path $OutputDir "summary.md"

function Write-StepLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8
}

function Invoke-Step {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    Write-StepLog "[STEP] $Name"
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments *>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    foreach ($item in $output) {
        $line = $item.ToString()
        Write-Host $line
        Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8
    }
    if ($exitCode -ne 0) {
        throw "Step failed: $Name"
    }
    Write-StepLog "[OK] $Name"
}

function Test-DemoHealth {
    try {
        $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 10
        return [bool]$health.ok
    } catch {
        return $false
    }
}

Write-StepLog "[INFO] Acceptance precheck started. base_url=$BaseUrl label=$ReportLabel"

if (-not $SkipDifyRecover) {
    Invoke-Step "Recover Dify 8081" (Join-Path $PSScriptRoot "recover_dify_8081.ps1")
} else {
    Write-StepLog "[SKIP] Recover Dify 8081"
}

if (-not (Test-DemoHealth)) {
    Invoke-Step "Start local Demo" (Join-Path $PSScriptRoot "start_dify_rag_local.ps1")
} else {
    Write-StepLog "[OK] Local Demo already healthy"
}

Invoke-Step "Record runtime snapshot" (Join-Path $PSScriptRoot "run_runtime_check_once.ps1") @(
    "-BaseUrl", $BaseUrl,
    "-ReportLabel", $ReportLabel,
    "-LogFile", (Join-Path $OutputDir "runtime_check.log")
)

Invoke-Step "Verify Dify acceptance route" (Join-Path $PSScriptRoot "verify_acceptance_route.ps1") @(
    "-BaseUrl", $BaseUrl
)

$backupNote = "Skipped"
if (-not $SkipBackup) {
    Invoke-Step "Backup Dify acceptance state" (Join-Path $PSScriptRoot "backup_dify_acceptance.ps1")
    $backupNote = "Created under artifacts/backups/dify/"
} else {
    Write-StepLog "[SKIP] Backup Dify acceptance state"
}

@(
    '# Acceptance Precheck Summary'
    ''
    ('- generated_at: `{0}`' -f (Get-Date).ToString('s'))
    ('- base_url: `{0}`' -f $BaseUrl)
    ('- report_label: `{0}`' -f $ReportLabel)
    ('- log_file: `{0}`' -f $logFile)
    ('- runtime_report: `artifacts/runtime/reports/runtime_{0}_summary.md`' -f $ReportLabel)
    ('- backup: `{0}`' -f $backupNote)
    ''
    '## Result'
    ''
    'All configured precheck steps completed.'
    ''
    '## Suggested Evidence To Keep'
    ''
    ('- This precheck directory: `{0}`' -f $OutputDir)
    '- Runtime snapshots and reports: `artifacts/runtime/`'
    '- Dify local backup: `artifacts/backups/dify/`'
    '- Screenshot evidence: `artifacts/screenshots/acceptance_20260609/`'
) | Set-Content -LiteralPath $summaryFile -Encoding UTF8

Write-StepLog "[OK] Acceptance precheck completed"
Write-Host "Summary : $summaryFile"
Write-Host "Log     : $logFile"
