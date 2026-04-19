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

function Test-OpenMetadataReachable {
  param([string]$BaseUrl)
  try {
    Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec 3 | Out-Null
    return $true
  } catch {
    return $false
  }
}

function Get-OpenMetadataBaseUrl {
  if ($env:OPENMETADATA_BASE_URL -and $env:OPENMETADATA_BASE_URL.Trim().Length -gt 0) {
    return $env:OPENMETADATA_BASE_URL.Trim()
  }
  return "http://localhost:8585/api/v1"
}

function Get-OpenMetadataToken {
  if ($env:OPENMETADATA_JWT_TOKEN -and $env:OPENMETADATA_JWT_TOKEN.Trim().Length -gt 0) {
    return $env:OPENMETADATA_JWT_TOKEN.Trim()
  }
  if ($env:OPENMETADATA_TOKEN -and $env:OPENMETADATA_TOKEN.Trim().Length -gt 0) {
    return $env:OPENMETADATA_TOKEN.Trim()
  }
  $generated = python ".\\scripts\\infra\\generate_om_jwt.py" --ttl-hours 2
  if (-not $generated) {
    throw "No se pudo obtener OPENMETADATA_JWT_TOKEN ni generar uno temporal."
  }
  return $generated.Trim()
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot
. ".\\scripts\\load_env.ps1" -Path ".\\.env" -Quiet

if (-not $SkipPipInstall) {
  python -m pip install -r ".\\requirements-dev.txt"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ExportOutput) | Out-Null
if ($ReportOutput) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReportOutput) | Out-Null
}

$pfJob = $null
try {
  $baseUrl = Get-OpenMetadataBaseUrl
  if (-not (Test-OpenMetadataReachable -BaseUrl $baseUrl) -and ($baseUrl -match "localhost|127\.0\.0\.1")) {
    $pfJob = Start-OmPortForward
  }

  $token = Get-OpenMetadataToken
  python ".\\scripts\\infra\\bootstrap_governance.py" --base-url $baseUrl --token $token

  $env:OPENMETADATA_BASE_URL = $baseUrl
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
