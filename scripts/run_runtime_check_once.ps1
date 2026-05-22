param(
    [string]$BaseUrl = "http://127.0.0.1:8091",
    [string]$PythonExe = "",
    [string]$ReportLabel = "latest",
    [string]$LogFile = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $PythonExe) {
    $PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $PythonExe)) {
        $PythonExe = "D:\Grammar\python\python.exe"
    }
}

if ($LogFile) {
    $logDir = Split-Path -Parent $LogFile
    if ($logDir) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    }
}

function Write-LogLine {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    if ($LogFile) {
        Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
    }
}

function Invoke-LoggedCommand {
    param(
        [string]$Executable,
        [string[]]$Arguments
    )
    $allOutput = & $Executable @Arguments 2>&1
    foreach ($item in $allOutput) {
        $line = $item.ToString()
        Write-Host $line
        if ($LogFile) {
            Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
        }
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Executable $($Arguments -join ' ')"
    }
}

Write-LogLine "[INFO] Runtime check started. base_url=$BaseUrl label=$ReportLabel"
Write-LogLine "[INFO] Using python: $PythonExe"
Write-LogLine "[INFO] Recording runtime snapshot..."
Invoke-LoggedCommand $PythonExe @(
    (Join-Path $RepoRoot "scripts\record_runtime_snapshot.py"),
    "--base-url", $BaseUrl
)

Write-LogLine "[INFO] Building runtime summary..."
Invoke-LoggedCommand $PythonExe @(
    (Join-Path $RepoRoot "scripts\build_runtime_report.py"),
    "--label", $ReportLabel
)

Write-LogLine "[OK] runtime check completed."
