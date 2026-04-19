param(
  [switch]$SkipPipInstall,
  [string]$PlanOutput = ".\\tmp_pytest\\workflow_first_plan.json"
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Start-OmPortForward {
  $job = Start-Job -ScriptBlock { kubectl port-forward deployment/openmetadata 8585:8585 }
  Start-Sleep -Seconds 3
  return $job
}

function Stop-OmPortForward {
  param($Job)
  if ($null -ne $Job) {
    Stop-Job $Job -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $Job -Force -ErrorAction SilentlyContinue | Out-Null
  }
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $PlanOutput) | Out-Null

if (-not $SkipPipInstall) {
  Write-Host "[0/5] Dependencias Python del repositorio..."
  python -m pip install -r ".\requirements-dev.txt"
}

Write-Host "[1/5] Infraestructura base (kind + helm + postgres en k8s)..."
powershell -ExecutionPolicy Bypass -File ".\scripts\infra\launch_infra.ps1"

Write-Host "[2/5] Ingesta tecnica Postgres..."
powershell -ExecutionPolicy Bypass -File ".\scripts\infra\ingest_postgres.ps1"

Write-Host "[3/5] Custom properties + tags..."
$pfJob = $null
try {
  $pfJob = Start-OmPortForward
  $token = python ".\scripts\infra\generate_om_jwt.py" --ttl-hours 2
  python ".\scripts\infra\bootstrap_governance.py" --base-url "http://localhost:8585/api/v1" --token $token

  Write-Host "[4/5] Preparar workflow canónico..."
  $env:OPENMETADATA_BASE_URL = "http://localhost:8585/api/v1"
  $env:OPENMETADATA_JWT_TOKEN = $token

  Write-Host "[5/5] Dry-run del workflow (refresca hoja y genera plan)..."
  $workflow = python -m om_dcat_sync workflow run --dry-run --plan-output $PlanOutput | ConvertFrom-Json
} finally {
  Stop-OmPortForward -Job $pfJob
}

$plannedCount = 0
if ($null -ne $workflow.sync -and $null -ne $workflow.sync.planned) {
  $plannedCount = ($workflow.sync.planned | Measure-Object).Count
}

$summary = @{
  output = $PlanOutput
  dry_run = $workflow.workflow.dry_run
  sheet_valid = $workflow.workflow.sheet_valid
  tables_discovered = $workflow.workflow.tables_discovered
  sheet_rows_loaded = $workflow.workflow.sheet_rows_loaded
  planned_changes = $plannedCount
}
$summary | ConvertTo-Json -Depth 6
