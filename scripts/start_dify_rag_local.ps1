$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env.dify_rag"
$EnvTemplate = Join-Path $RepoRoot ".env.dify_rag.example"
$RuntimeDir = Join-Path $RepoRoot "artifacts\local-dify-rag"
$RuntimeFile = Join-Path $RuntimeDir "runtime.json"
$LaunchPyFile = Join-Path $RuntimeDir "launch_dify_rag.py"
$LaunchEnvFile = Join-Path $RuntimeDir "launch_env.json"
$LogDir = Join-Path $RepoRoot "logs"
$LogFile = Join-Path $LogDir "dify_rag.log"
$ErrFile = Join-Path $LogDir "dify_rag.err.log"
$AppDir = Join-Path $RepoRoot "web_demo"

function Resolve-PythonExe {
    $candidates = @(
        (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
        "D:\Grammar\python\python.exe",
        "D:\newwork\lab-safe-assistant-workspace\lab-safe-assistant-github\.venv312\Scripts\python.exe",
        "python"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -ne "python" -and -not (Test-Path -LiteralPath $candidate)) { continue }
        try {
            $cmd = "import fastapi, uvicorn, requests, sys; print(sys.executable)"
            $candidatePath = [string]$candidate
            if ($candidatePath -eq "python") {
                $out = & python -c $cmd 2>$null
            } else {
                $out = & $candidatePath -c $cmd 2>$null
            }
            if ($LASTEXITCODE -eq 0) {
                return $candidatePath
            }
        } catch {}
    }
    throw "Cannot find a Python interpreter with required modules: fastapi, uvicorn, requests"
}

function Read-EnvFile {
    param([string]$Path)
    $values = @{}
    foreach ($line in Get-Content -Path $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $pair = $trimmed -split '=', 2
        if ($pair.Count -eq 2) { $values[$pair[0].Trim()] = $pair[1].Trim() }
    }
    return $values
}

function Wait-HttpReady {
    param([string]$Url, [int]$RetryCount = 25, [int]$SleepSeconds = 1)
    for ($i = 0; $i -lt $RetryCount; $i++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return $true }
        } catch {}
        Start-Sleep -Seconds $SleepSeconds
    }
    return $false
}

if (-not (Test-Path $EnvFile)) {
    Copy-Item -Path $EnvTemplate -Destination $EnvFile -Force
    Write-Host "[WARN] Created env file from template: $EnvFile"
    Write-Host "[WARN] Fill DIFY_APP_API_KEY for real Dify answers. The app can still run in structured fallback mode."
}

$envMap = Read-EnvFile -Path $EnvFile
$demoPort = 8088
if ($envMap.ContainsKey('DEMO_PORT') -and $envMap['DEMO_PORT']) { $demoPort = [int]$envMap['DEMO_PORT'] }

$existingConn = Get-NetTCPConnection -State Listen -LocalPort $demoPort -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existingConn) {
    $owner = Get-Process -Id $existingConn.OwningProcess -ErrorAction SilentlyContinue
    $ownerLabel = if ($owner) { "$($owner.ProcessName)($($owner.Id))" } else { "pid=$($existingConn.OwningProcess)" }
    throw "Port $demoPort is already occupied by $ownerLabel"
}

New-Item -ItemType Directory -Force -Path $RuntimeDir, $LogDir | Out-Null
if (Test-Path $LogFile) { Remove-Item $LogFile -Force -ErrorAction SilentlyContinue }
if (Test-Path $ErrFile) { Remove-Item $ErrFile -Force -ErrorAction SilentlyContinue }

$envPayload = [ordered]@{
    DIFY_BASE_URL = [string]($envMap['DIFY_BASE_URL'])
    DIFY_APP_API_KEY = [string]($envMap['DIFY_APP_API_KEY'])
    DIFY_TIMEOUT = [string]($envMap['DIFY_TIMEOUT'])
    DEMO_PORT = [string]$demoPort
    DEFAULT_TOP_K = [string]($envMap['DEFAULT_TOP_K'])
    LOW_CONFIDENCE_TOP_SCORE = [string]($envMap['LOW_CONFIDENCE_TOP_SCORE'])
    KB_IMPORT_SUCCESS_COUNT = [string]($envMap['KB_IMPORT_SUCCESS_COUNT'])
    KB_CHUNK_IMPORT_COUNT = [string]($envMap['KB_CHUNK_IMPORT_COUNT'])
    KB_EXTERNAL_IMPORT_COUNT = [string]($envMap['KB_EXTERNAL_IMPORT_COUNT'])
    ENABLE_EMBEDDING = [string]($envMap['ENABLE_EMBEDDING'])
    SEMANTIC_WEIGHT = [string]($envMap['SEMANTIC_WEIGHT'])
    WORKDIR = $AppDir
}
$envPayload | ConvertTo-Json -Depth 4 | Set-Content -Path $LaunchEnvFile -Encoding UTF8

$pyLines = @(
    'import json, os, sys, uvicorn',
    'from pathlib import Path',
    'cfg = json.loads(Path(__file__).with_name("launch_env.json").read_text(encoding="utf-8-sig"))',
    'for key, value in cfg.items():',
    '    if key == "WORKDIR":',
    '        continue',
    '    os.environ[key] = str(value or "")',
    'os.chdir(cfg["WORKDIR"])',
    'sys.path.insert(0, str(Path(cfg["WORKDIR"]).parent))',
    'uvicorn.run("web_demo.app:app", host="127.0.0.1", port=int(cfg["DEMO_PORT"]))'
)
Set-Content -Path $LaunchPyFile -Value $pyLines -Encoding UTF8

$PythonExe = Resolve-PythonExe
$proc = Start-Process -FilePath $PythonExe -ArgumentList @($LaunchPyFile) -WorkingDirectory $AppDir -RedirectStandardOutput $LogFile -RedirectStandardError $ErrFile -PassThru -WindowStyle Hidden

if (-not (Wait-HttpReady -Url "http://127.0.0.1:$demoPort/health" -RetryCount 25 -SleepSeconds 1)) {
    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
    throw "Dify RAG app failed to start. Check log: $LogFile ; err: $ErrFile"
}

$runtime = [ordered]@{
    started_at = (Get-Date -Format s)
    demo_port = $demoPort
    pid = $proc.Id
    url = "http://127.0.0.1:$demoPort"
    env_file = $EnvFile
    launch_file = $LaunchPyFile
    python_exe = $PythonExe
    log_file = $LogFile
    err_file = $ErrFile
    dify_configured = -not [string]::IsNullOrWhiteSpace([string]($envMap['DIFY_APP_API_KEY']))
}
$runtime | ConvertTo-Json -Depth 4 | Set-Content -Path $RuntimeFile -Encoding UTF8

Write-Host "[OK] Dify RAG app started"
Write-Host "URL       : http://127.0.0.1:$demoPort"
Write-Host "Health    : http://127.0.0.1:$demoPort/health"
Write-Host "Dify key  : $(if($runtime.dify_configured){'configured'}else{'missing/fallback'})"
Write-Host "Runtime   : $RuntimeFile"
Write-Host "Python    : $PythonExe"
Write-Host "Log       : $LogFile"
Write-Host "Err Log   : $ErrFile"
