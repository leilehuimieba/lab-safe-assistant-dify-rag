param(
    [string]$TaskName = "LabSafeAssistant-DailyRuntimeCheck"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "[INFO] Scheduled task not found: $TaskName"
    exit 0
}

$info = Get-ScheduledTaskInfo -TaskName $TaskName
$action = $task.Actions | Select-Object -First 1
$trigger = $task.Triggers | Select-Object -First 1

Write-Host "TaskName: $TaskName"
Write-Host "State: $($task.State)"
Write-Host "LastRunTime: $($info.LastRunTime)"
Write-Host "LastTaskResult: $($info.LastTaskResult)"
Write-Host "NextRunTime: $($info.NextRunTime)"
Write-Host "Execute: $($action.Execute)"
Write-Host "Arguments: $($action.Arguments)"
Write-Host "Trigger: $($trigger.StartBoundary)"
