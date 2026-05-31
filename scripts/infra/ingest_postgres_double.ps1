param(
  [string[]]$ServiceNames = @("postgres_demo_service", "postgres_validation_service"),
  [string]$DbUser = "om_demo",
  [string]$DbPassword = "om_demo",
  [string]$DbHostPort = "",
  [string]$DbName = "opendata_demo"
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

$summaries = @()
foreach ($serviceName in $ServiceNames) {
  if (-not $serviceName -or $serviceName.Trim().Length -eq 0) {
    continue
  }
  $resolvedServiceName = $serviceName.Trim()
  Write-Host "Ingesta tecnica PostgreSQL para servicio '$resolvedServiceName'..."
  $args = @(
    "-ExecutionPolicy", "Bypass",
    "-File", ".\scripts\infra\ingest_postgres.ps1",
    "-ServiceName", $resolvedServiceName,
    "-DbUser", $DbUser,
    "-DbPassword", $DbPassword,
    "-DbName", $DbName
  )
  if ($DbHostPort -and $DbHostPort.Trim().Length -gt 0) {
    $args += @("-DbHostPort", $DbHostPort.Trim())
  }

  powershell @args
  if ($LASTEXITCODE -ne 0) {
    throw "La ingesta tecnica fallo para el servicio '$resolvedServiceName'."
  }

  $summaries += @{
    service_name = $resolvedServiceName
    database = $DbName
  }
}

@{
  operation = "ingest_postgres_double"
  services = $summaries
  service_count = $summaries.Count
} | ConvertTo-Json -Depth 6
