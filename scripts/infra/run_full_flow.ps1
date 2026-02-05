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

Write-Host "[1/4] Infraestructura base (kind + helm + postgres en k8s)..."
powershell -ExecutionPolicy Bypass -File ".\scripts\infra\launch_infra.ps1"

Write-Host "[2/4] Ingesta tecnica Postgres..."
powershell -ExecutionPolicy Bypass -File ".\scripts\infra\ingest_postgres.ps1"

Write-Host "[3/4] Custom properties + tags..."
$pfJob = $null
try {
  $pfJob = Start-OmPortForward
  $token = python ".\scripts\infra\generate_om_jwt.py" --ttl-hours 2
  python ".\scripts\infra\bootstrap_governance.py" --base-url "http://localhost:8585/api/v1" --token $token

  Write-Host "[4/4] Dry-run tfm_ingestor..."
  if (-not $SkipPipInstall) {
    python -m pip install -e "tfm_ingestor[dev]"
  }
  $env:OPENMETADATA_BASE_URL = "http://localhost:8585/api/v1"
  $env:OPENMETADATA_JWT_TOKEN = $token
  python -m tfm_ingestor --dry-run
} finally {
  Stop-OmPortForward -Job $pfJob
}
