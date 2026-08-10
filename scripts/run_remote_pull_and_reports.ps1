# 一次性完成"回收云端 7x24 快照 + 重建每日/滚动报表"，供计划任务调用。
#
# 背景：2026-07-28 至 2026-08-09 期间云主机采集一直正常，但本地回收脚本只能手动
# 执行，结果 12 天的真实运行证据一直留在服务器上没有并入本地档案。本脚本把回收和
# 报表重建串成一步，配合 scripts\register_weekly_remote_pull.ps1 定期触发。

param(
    [string]$PythonExe = "",
    [string]$LogFile = "",
    [string]$LedgerStartDate = "2026-07-01"
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
if (-not $LogFile) {
    $LogFile = Join-Path $RepoRoot "artifacts\runtime\logs\remote_pull.log"
}

$logDir = Split-Path -Parent $LogFile
if ($logDir) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

function Write-LogLine {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
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
        Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Executable $($Arguments -join ' ')"
    }
}

Write-LogLine "[INFO] Remote pull + report rebuild started."
Write-LogLine "[INFO] Using python: $PythonExe"

Write-LogLine "[INFO] Pulling remote runtime snapshots..."
Invoke-LoggedCommand "powershell.exe" @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $PSScriptRoot "pull_remote_runtime_snapshots.ps1")
)

Write-LogLine "[INFO] Rebuilding per-day evidence ledger..."
Invoke-LoggedCommand $PythonExe @(
    (Join-Path $RepoRoot "scripts\build_daily_runtime_reports.py"),
    "--daily-output-dir", (Join-Path $RepoRoot "artifacts\runtime\daily"),
    "--index-csv", (Join-Path $RepoRoot "artifacts\runtime\daily_index.csv"),
    "--start-date", $LedgerStartDate
)

Write-LogLine "[INFO] Rebuilding rolling summaries..."
Invoke-LoggedCommand $PythonExe @(
    (Join-Path $RepoRoot "scripts\build_runtime_report.py"),
    "--label", "latest"
)
Invoke-LoggedCommand $PythonExe @(
    (Join-Path $RepoRoot "scripts\build_runtime_report.py"),
    "--label", "cloud_current",
    "--date-from", "2026-07-23"
)

Write-LogLine "[OK] remote pull + report rebuild completed."
