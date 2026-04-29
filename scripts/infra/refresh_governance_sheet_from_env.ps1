param(
  [string]$BaseUrl = "",
  [string]$Output = ".\tfm_ingestor\config\gold_governance.csv",
  [switch]$SkipPipInstall
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Import-LocalEnv {
  param([string]$RepoRoot)
  $loader = Join-Path $RepoRoot "scripts\load_env.ps1"
  $envPath = Join-Path $RepoRoot ".env"
  if (Test-Path -LiteralPath $loader) {
    . $loader -Path $envPath -Quiet
  }
}

function Get-OpenMetadataBaseUrl {
  param([string]$Value)
  if ($Value -and $Value.Trim().Length -gt 0) {
    return $Value.Trim().TrimEnd("/")
  }
  if ($env:OPENMETADATA_BASE_URL -and $env:OPENMETADATA_BASE_URL.Trim().Length -gt 0) {
    return $env:OPENMETADATA_BASE_URL.Trim().TrimEnd("/")
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
  $generated = python ".\scripts\infra\generate_om_jwt.py" --ttl-hours 2
  if (-not $generated) {
    throw "No se pudo obtener OPENMETADATA_JWT_TOKEN, OPENMETADATA_TOKEN ni generar uno temporal."
  }
  return $generated.Trim()
}

function Test-OpenMetadataHttp {
  param([string]$BaseUrl)
  try {
    Invoke-WebRequest -Uri "$BaseUrl/system/health" -UseBasicParsing -TimeoutSec 5 | Out-Null
    return $true
  } catch {
    return $false
  }
}

function Start-OmPortForwardIfNeeded {
  param([string]$BaseUrl)
  if ($BaseUrl -notlike "http://localhost:8585*" -and $BaseUrl -notlike "http://127.0.0.1:8585*") {
    return $null
  }
  if (Test-OpenMetadataHttp -BaseUrl $BaseUrl) {
    Write-Host "OpenMetadata ya responde en $BaseUrl."
    return $null
  }
  Write-Host "Abriendo port-forward temporal a OpenMetadata..."
  $job = Start-Job -ScriptBlock {
    kubectl port-forward deployment/openmetadata 8585:8585
  }
  Start-Sleep -Seconds 4
  if (-not (Test-OpenMetadataHttp -BaseUrl $BaseUrl)) {
    Stop-OmPortForward -Job $job
    throw "No se pudo abrir el port-forward temporal a OpenMetadata."
  }
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
Import-LocalEnv -RepoRoot $repoRoot

if (-not $SkipPipInstall) {
  python -m pip install -r ".\requirements-dev.txt"
}

$resolvedBaseUrl = Get-OpenMetadataBaseUrl -Value $BaseUrl
$token = Get-OpenMetadataToken
$pfJob = $null

try {
  $pfJob = Start-OmPortForwardIfNeeded -BaseUrl $resolvedBaseUrl
  python -m om_dcat_sync generate-governance-sheet `
    --base-url $resolvedBaseUrl `
    --token $token `
    --output $Output
} finally {
  Stop-OmPortForward -Job $pfJob
}
