# 从远程主监测环境（云服务器）拉取 7x24 运行快照，去重合并进本地 git 仓库。
#
# 连接参数从 scripts\.remote_runtime.local.json 读取（该文件已 gitignore，不入库，
# 因为其中含服务器公网 IP 与 SSH key 路径）。首次使用请复制
# scripts\.remote_runtime.local.json.example 为 scripts\.remote_runtime.local.json
# 并填入真实值，或用下面的参数覆盖。

param(
    [string]$RemoteHost = "",
    [string]$RemoteUser = "",
    [string]$KeyPath = "",
    [string]$RemotePath = "",
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $PSScriptRoot ".remote_runtime.local.json"

if ((-not $RemoteHost -or -not $RemoteUser -or -not $KeyPath -or -not $RemotePath) -and (Test-Path $ConfigPath)) {
    $config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
    if (-not $RemoteHost) { $RemoteHost = $config.RemoteHost }
    if (-not $RemoteUser) { $RemoteUser = $config.RemoteUser }
    if (-not $KeyPath) { $KeyPath = $config.KeyPath }
    if (-not $RemotePath) { $RemotePath = $config.RemotePath }
}

if (-not $RemoteHost -or -not $RemoteUser -or -not $KeyPath -or -not $RemotePath) {
    throw "缺少远程连接配置。请创建 scripts\.remote_runtime.local.json（参考 .example 文件）或通过参数传入 -RemoteHost -RemoteUser -KeyPath -RemotePath"
}

if (-not $PythonExe) {
    $PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $PythonExe)) {
        $PythonExe = "D:\Grammar\python\python.exe"
    }
}

$StagingDir = Join-Path $RepoRoot "artifacts\runtime\_remote_pull_staging"
New-Item -ItemType Directory -Force -Path $StagingDir | Out-Null
$StagedJsonl = Join-Path $StagingDir "health_snapshots.remote.jsonl"

Write-Host "[INFO] Pulling remote snapshot file from ${RemoteUser}@${RemoteHost}:${RemotePath}..."
$remoteFile = "${RemoteUser}@${RemoteHost}:${RemotePath}/artifacts/runtime/health_snapshots.jsonl"
& scp -i $KeyPath $remoteFile $StagedJsonl
if ($LASTEXITCODE -ne 0) {
    throw "scp failed with exit code $LASTEXITCODE"
}

Write-Host "[INFO] Merging into local health_snapshots.jsonl/.csv..."
& $PythonExe (Join-Path $RepoRoot "scripts\merge_runtime_snapshots.py") --remote-jsonl $StagedJsonl
if ($LASTEXITCODE -ne 0) {
    throw "merge_runtime_snapshots.py failed with exit code $LASTEXITCODE"
}

Write-Host "[OK] remote runtime snapshots pulled and merged."
