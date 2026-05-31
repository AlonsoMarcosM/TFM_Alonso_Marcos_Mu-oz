param(
  [string[]]$ServiceNames = @("postgres_demo_service", "postgres_validation_service"),
  [string]$BaseUrl = ""
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
  Write-Host "Vaciando servicio PostgreSQL '$resolvedServiceName' en OpenMetadata..."
  if ($BaseUrl -and $BaseUrl.Trim().Length -gt 0) {
    powershell -ExecutionPolicy Bypass -File ".\scripts\infra\clear_openmetadata_postgres_source.ps1" `
      -ServiceName $resolvedServiceName `
      -BaseUrl $BaseUrl
  } else {
    powershell -ExecutionPolicy Bypass -File ".\scripts\infra\clear_openmetadata_postgres_source.ps1" `
      -ServiceName $resolvedServiceName
  }
  $summaries += @{ service_name = $resolvedServiceName }
}

@{
  operation = "clear_openmetadata_postgres_sources"
  services = $summaries
  service_count = $summaries.Count
} | ConvertTo-Json -Depth 6
