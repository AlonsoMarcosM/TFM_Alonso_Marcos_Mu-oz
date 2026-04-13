param(
  [switch]$SkipPipInstall
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
  python -m om_dcat_sync workflow run --dry-run
} finally {
  Stop-OmPortForward -Job $pfJob
}
