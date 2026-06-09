param(
    [string]$OutputRoot = "",
    [string]$DifyComposeDir = "D:\newwork\lab-safe-assistant-workspace\lab-safe-assistant-github\local_env\dify\docker",
    [string]$ProjectName = "docker",
    [string]$PostgresContainer = "docker-db_postgres-1",
    [string]$Database = "dify",
    [string]$DatabaseUser = "postgres"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $RepoRoot "artifacts\backups\dify"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $OutputRoot $stamp
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

function Invoke-Logged {
    param(
        [string]$Executable,
        [string[]]$Arguments,
        [string]$OutFile = ""
    )

    if ($OutFile) {
        $output = & $Executable @Arguments 2>&1
        $output | Set-Content -LiteralPath $OutFile -Encoding UTF8
    } else {
        & $Executable @Arguments
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Executable $($Arguments -join ' ')"
    }
}

function Invoke-PsqlQueryFile {
    param(
        [string]$Sql,
        [string]$OutFile,
        [string]$Name
    )

    $localSql = Join-Path $backupDir "$Name.sql"
    $containerSql = "/tmp/lab_safe_${stamp}_${Name}.sql"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($localSql, $Sql, $utf8NoBom)

    Invoke-Logged "docker" @("cp", $localSql, "${PostgresContainer}:$containerSql")
    Invoke-Logged "docker" @(
        "exec", $PostgresContainer,
        "psql", "-v", "ON_ERROR_STOP=1",
        "-U", $DatabaseUser, "-d", $Database,
        "-A", "-F", "`t",
        "-f", $containerSql
    ) $OutFile
}

if (-not (Test-Path -LiteralPath $DifyComposeDir)) {
    throw "Dify compose directory not found: $DifyComposeDir"
}

$containerId = docker ps -q -f "name=^/${PostgresContainer}$"
if (-not $containerId) {
    throw "Postgres container is not running: $PostgresContainer"
}

Write-Host "[INFO] Backup directory: $backupDir"

$dbDump = Join-Path $backupDir "dify_pg_dump.sql"
Write-Host "[INFO] Dumping Dify Postgres database..."
Invoke-Logged "docker" @(
    "exec", $PostgresContainer,
    "pg_dump", "-U", $DatabaseUser, "-d", $Database,
    "--no-owner", "--no-privileges", "--format=plain"
) $dbDump

$routeSql = @"
select pm.model_name,
       pm.model_type,
       pmc.encrypted_config::json ->> 'endpoint_url' as endpoint_url,
       pmc.encrypted_config::json ->> 'endpoint_model_name' as endpoint_model_name
from provider_models pm
left join provider_model_credentials pmc on pm.credential_id = pmc.id
where pm.model_name in ('gpt-5.3-codex', 'deepseek-v4-pro')
order by pm.model_name, pm.model_type;
"@
$routeFile = Join-Path $backupDir "dify_model_route_snapshot.tsv"
Write-Host "[INFO] Exporting non-secret model route snapshot..."
Invoke-PsqlQueryFile -Sql $routeSql -OutFile $routeFile -Name "model_route_snapshot"

$oldUrlSql = @"
select 'provider_model_credentials' as table_name, count(*) as old_url_hits
from provider_model_credentials where encrypted_config like '%api-vip.codex-for.me%'
union all
select 'provider_credentials', count(*) from provider_credentials where encrypted_config like '%api-vip.codex-for.me%'
union all
select 'load_balancing_model_configs', count(*) from load_balancing_model_configs where encrypted_config like '%api-vip.codex-for.me%';
"@
$oldUrlFile = Join-Path $backupDir "old_route_residue_check.tsv"
Write-Host "[INFO] Checking old route residue..."
Invoke-PsqlQueryFile -Sql $oldUrlSql -OutFile $oldUrlFile -Name "old_route_residue_check"

$composePs = Join-Path $backupDir "dify_compose_ps.txt"
Push-Location $DifyComposeDir
try {
    Invoke-Logged "docker" @("compose", "-p", $ProjectName, "ps") $composePs
} finally {
    Pop-Location
}

$manifest = Join-Path $backupDir "manifest.txt"
@(
    "created_at=$((Get-Date).ToString('s'))"
    "repo_root=$RepoRoot"
    "dify_compose_dir=$DifyComposeDir"
    "project_name=$ProjectName"
    "postgres_container=$PostgresContainer"
    "database=$Database"
    "db_dump=$dbDump"
    "route_snapshot=$routeFile"
    "old_route_check=$oldUrlFile"
    "compose_ps=$composePs"
    "note=Database dump is local acceptance evidence and may contain encrypted credentials. Do not commit."
) | Set-Content -LiteralPath $manifest -Encoding UTF8

Write-Host "[OK] Dify backup completed"
Write-Host "Backup dir : $backupDir"
Write-Host "DB dump    : $dbDump"
Write-Host "Route file : $routeFile"
