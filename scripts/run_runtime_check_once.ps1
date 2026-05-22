$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RepoRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "D:\Grammar\python\python.exe"
}

Write-Host "[INFO] Recording runtime snapshot..."
& $PythonExe (Join-Path $RepoRoot "scripts\record_runtime_snapshot.py")

Write-Host "[INFO] Building runtime summary..."
& $PythonExe (Join-Path $RepoRoot "scripts\build_runtime_report.py") --label latest

Write-Host "[OK] runtime check completed."
