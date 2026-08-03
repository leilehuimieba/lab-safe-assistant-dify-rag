param(
    [string]$PythonExe = "",
    [string]$IsoWeek = "",
    [string]$BaseUrl = "http://127.0.0.1:8088"
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

if (-not $IsoWeek) {
    $today = Get-Date
    $calendar = [System.Globalization.CultureInfo]::InvariantCulture.Calendar
    $week = $calendar.GetWeekOfYear(
        $today,
        [System.Globalization.CalendarWeekRule]::FirstFourDayWeek,
        [DayOfWeek]::Monday
    )
    $isoWeek = "{0}W{1:00}" -f $today.Year, $week
}

$notesPath = Join-Path $RepoRoot "artifacts\runtime\notes\weekly_issues_${IsoWeek}.md"

& $PythonExe (Join-Path $RepoRoot "scripts\record_runtime_snapshot.py") "--base-url" $BaseUrl
if ($LASTEXITCODE -ne 0) { throw "record_runtime_snapshot.py failed" }

& $PythonExe (Join-Path $RepoRoot "scripts\build_runtime_report.py") `
    "--label" $IsoWeek `
    "--iso-week" $IsoWeek `
    "--notes-output" $notesPath
if ($LASTEXITCODE -ne 0) { throw "build_runtime_report.py failed" }

Write-Host "[OK] Weekly runtime report built for $IsoWeek"
Write-Host "[OK] Notes file: $notesPath"
