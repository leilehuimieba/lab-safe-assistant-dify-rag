param(
    [string]$TaskName = "LabSafeAssistant-DailyRuntimeCheck",
    [string]$RunTime = "08:30",
    [string]$BaseUrl = "http://127.0.0.1:8091",
    [string]$PythonExe = "",
    [string]$ReportLabel = "latest"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ($RunTime -notmatch '^\d{2}:\d{2}$') {
    throw "RunTime must be in HH:mm format, for example 08:30"
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $RepoRoot "scripts\run_runtime_check_once.ps1"
$LogFile = Join-Path $RepoRoot "artifacts\runtime\logs\daily_runtime_check.log"
$LogDir = Split-Path -Parent $LogFile
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$argList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", ('"{0}"' -f $Runner),
    "-BaseUrl", ('"{0}"' -f $BaseUrl),
    "-ReportLabel", ('"{0}"' -f $ReportLabel),
    "-LogFile", ('"{0}"' -f $LogFile)
)
if ($PythonExe) {
    $argList += @("-PythonExe", ('"{0}"' -f $PythonExe))
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ($argList -join " ")
$trigger = New-ScheduledTaskTrigger -Daily -At $RunTime
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$description = "实验室安全小助手每日运行检查：采集 health/meta/stats 快照并更新 runtime 摘要"

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description $description `
    -Force | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName

Write-Host "[OK] Scheduled task registered."
Write-Host ("TaskName: {0}" -f $TaskName)
Write-Host ("State: {0}" -f $task.State)
Write-Host ("NextRunTime: {0}" -f $info.NextRunTime)
Write-Host ("BaseUrl: {0}" -f $BaseUrl)
Write-Host ("ReportLabel: {0}" -f $ReportLabel)
Write-Host ("LogFile: {0}" -f $LogFile)
