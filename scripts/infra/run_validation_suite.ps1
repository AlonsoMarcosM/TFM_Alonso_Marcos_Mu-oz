param(
  [switch]$SkipPipInstall,
  [switch]$SkipPrePushChecks,
  [string]$RuntimeReportOutput = ".\\tmp_pytest\\runtime_validation_report.json",
  [string]$FirstWorkflowPlanOutput = ".\\tmp_pytest\\workflow_first_plan.json",
  [string]$SecondWorkflowPlanOutput = ".\\tmp_pytest\\workflow_second_plan.json",
  [string]$ExportOutput = ".\\tmp_pytest\\validation_suite_catalog.jsonld",
  [string]$ShaclReportOutput = ".\\tmp_pytest\\validation_suite_shacl_report.ttl",
  [string]$PrePushReportOutput = ".\\tmp_pytest\\pre_push_checks.json",
  [string]$SummaryOutput = ".\\tmp_pytest\\validation_suite_summary.json"
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

New-Item -ItemType Directory -Force -Path ".\\tmp_pytest" | Out-Null

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

  $first = python -m om_dcat_sync workflow run --allow-warnings --plan-output $FirstWorkflowPlanOutput --export-output $ExportOutput --report-output $ShaclReportOutput | ConvertFrom-Json
  $runtime = python -m om_dcat_sync validate-runtime --strict --output $RuntimeReportOutput | ConvertFrom-Json
  $second = python -m om_dcat_sync workflow run --allow-warnings --plan-output $SecondWorkflowPlanOutput --export-output $ExportOutput --report-output $ShaclReportOutput | ConvertFrom-Json

  $idempotenceOk = ($second.sync.applied -eq 0) -and (($second.sync.planned | Measure-Object).Count -eq 0) -and ($second.validation.conforms -eq $true)
  if (-not $idempotenceOk) {
    throw "La segunda ejecución del workflow no ha sido idempotente."
  }
} finally {
  Stop-OmPortForward -Job $pfJob
}

$prePush = $null
if (-not $SkipPrePushChecks) {
  powershell -ExecutionPolicy Bypass -File ".\\scripts\\quality\\pre_push_checks.ps1" -OutputPath $PrePushReportOutput | Out-Null
  $prePush = Get-Content -Raw $PrePushReportOutput | ConvertFrom-Json
}

$summary = @{
  runtime_validation = $runtime
  first_workflow = $first
  second_workflow = $second
  idempotence = @{
    conforms = $idempotenceOk
    second_applied = $second.sync.applied
    second_planned = ($second.sync.planned | Measure-Object).Count
  }
  pre_push_checks = $prePush
}

$summaryJson = $summary | ConvertTo-Json -Depth 8
Set-Content -Path $SummaryOutput -Value $summaryJson -Encoding utf8
$consoleSummary = @{
  output = $SummaryOutput
  runtime_conforms = $runtime.conforms
  technical_conforms = $runtime.technical.conforms
  governance_conforms = $runtime.governance.conforms
  first_applied = $first.sync.applied
  second_applied = $second.sync.applied
  second_planned = ($second.sync.planned | Measure-Object).Count
  idempotence_conforms = $idempotenceOk
  shacl_conforms = $second.validation.conforms
  shacl_warnings = $second.validation.warnings
  tables_exported = $second.validation.tables_exported
  preview_dataset_count = $second.validation.preview_dataset_count
  pre_push_checks_executed = ($null -ne $prePush)
}
$consoleSummary | ConvertTo-Json -Depth 6
