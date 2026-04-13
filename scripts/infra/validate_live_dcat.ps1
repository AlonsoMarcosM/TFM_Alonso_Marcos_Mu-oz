param(
  [switch]$SkipPipInstall,
  [string]$SheetPath = ".\\tfm_ingestor\\config\\gold_governance.csv",
  [string]$ExportOutput = ".\\tmp_pytest\\live_dcat_catalog.jsonld",
  [string]$ReportOutput = ".\\tmp_pytest\\live_dcat_validation_report.ttl",
  [switch]$StrictShacl
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
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
  python -m pip install -r ".\\requirements-dev.txt"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ExportOutput) | Out-Null
if ($ReportOutput) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReportOutput) | Out-Null
}

$pfJob = $null
try {
  $pfJob = Start-OmPortForward
  $token = python ".\\scripts\\infra\\generate_om_jwt.py" --ttl-hours 2
  python ".\\scripts\\infra\\bootstrap_governance.py" --base-url "http://localhost:8585/api/v1" --token $token

  $env:OPENMETADATA_BASE_URL = "http://localhost:8585/api/v1"
  $env:OPENMETADATA_JWT_TOKEN = $token

  $workflowArgs = @(
    "-m", "om_dcat_sync", "workflow", "run",
    "--sheet", $SheetPath,
    "--export-output", $ExportOutput,
    "--report-output", $ReportOutput
  )
  if (-not $StrictShacl) {
    $workflowArgs += "--allow-warnings"
  }
  python @workflowArgs
} finally {
  Stop-OmPortForward -Job $pfJob
}
