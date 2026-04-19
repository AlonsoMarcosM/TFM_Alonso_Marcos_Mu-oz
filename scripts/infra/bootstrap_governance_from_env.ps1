param(
  [string]$BaseUrl = "",
  [switch]$SkipPipInstall
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Get-OpenMetadataBaseUrl {
  param([string]$Value)
  if ($Value -and $Value.Trim().Length -gt 0) {
    return $Value.Trim()
  }
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
  $generated = python ".\scripts\infra\generate_om_jwt.py" --ttl-hours 2
  if (-not $generated) {
    throw "No se pudo obtener OPENMETADATA_JWT_TOKEN, OPENMETADATA_TOKEN ni generar uno temporal."
  }
  return $generated.Trim()
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot
. ".\scripts\load_env.ps1" -Path ".\.env" -Quiet

if (-not $SkipPipInstall) {
  python -m pip install -r ".\requirements-dev.txt"
}

$resolvedBaseUrl = Get-OpenMetadataBaseUrl -Value $BaseUrl
$token = Get-OpenMetadataToken

python ".\scripts\infra\bootstrap_governance.py" --base-url $resolvedBaseUrl --token $token
