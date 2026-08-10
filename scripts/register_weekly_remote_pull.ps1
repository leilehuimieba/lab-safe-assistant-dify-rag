param(
    [string]$TaskName = "LabSafeAssistant-WeeklyRemotePull",
    [string]$RunTime = "09:00",
    [string]$DayOfWeek = "Monday",
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ($RunTime -notmatch '^\d{2}:\d{2}$') {
    throw "RunTime must be in HH:mm format, for example 09:00"
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $RepoRoot "scripts\run_remote_pull_and_reports.ps1"
$LogFile = Join-Path $RepoRoot "artifacts\runtime\logs\remote_pull.log"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LogFile) | Out-Null

$argList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", ('"{0}"' -f $Runner),
    "-LogFile", ('"{0}"' -f $LogFile)
)
if ($PythonExe) {
    $argList += @("-PythonExe", ('"{0}"' -f $PythonExe))
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ($argList -join " ")
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At $RunTime
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$description = "每周从云主机回收 7x24 运行快照并重建每日/滚动报表（本地工作站为间歇性开机环境，StartWhenAvailable 保证开机后补跑；错过的周次不补写历史，只影响回收时点）"

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
Write-Host ("Schedule: {0} {1}" -f $DayOfWeek, $RunTime)
Write-Host ("NextRunTime: {0}" -f $info.NextRunTime)
Write-Host ("LogFile: {0}" -f $LogFile)
