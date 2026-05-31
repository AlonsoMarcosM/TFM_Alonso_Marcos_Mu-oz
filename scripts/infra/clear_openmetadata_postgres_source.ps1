param(
  [string]$ServiceName = "postgres_demo_service",
  [string]$BaseUrl = ""
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

function Get-HttpStatus {
  param($ErrorRecord)
  if ($ErrorRecord.Exception.Response -and $ErrorRecord.Exception.Response.StatusCode) {
    return [int]$ErrorRecord.Exception.Response.StatusCode.value__
  }
  return $null
}

function Invoke-OmApi {
  param(
    [string]$Method,
    [string]$Path,
    [string]$BaseUrl,
    [string]$Token
  )
  $headers = @{ Authorization = "Bearer $Token" }
  return Invoke-RestMethod -Uri "$BaseUrl$Path" -Headers $headers -Method $Method
}

function Get-DatabaseService {
  param(
    [string]$ServiceName,
    [string]$BaseUrl,
    [string]$Token
  )
  try {
    return Invoke-OmApi -Method "GET" -Path "/services/databaseServices/name/$ServiceName" -BaseUrl $BaseUrl -Token $Token
  } catch {
    if ((Get-HttpStatus -ErrorRecord $_) -eq 404) {
      return $null
    }
    throw
  }
}

function Get-ServiceTableCount {
  param(
    [string]$ServiceName,
    [string]$BaseUrl,
    [string]$Token
  )
  $tables = Invoke-OmApi -Method "GET" -Path "/tables?limit=1000" -BaseUrl $BaseUrl -Token $Token
  $items = @($tables.data | Where-Object { $_.fullyQualifiedName -like "$ServiceName.*" })
  return $items.Count
}

function Remove-DatabaseService {
  param(
    [string]$ServiceId,
    [string]$BaseUrl,
    [string]$Token
  )
  Invoke-OmApi -Method "DELETE" -Path "/services/databaseServices/$ServiceId`?recursive=true&hardDelete=true" -BaseUrl $BaseUrl -Token $Token | Out-Null
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot
Import-LocalEnv -RepoRoot $repoRoot

$resolvedBaseUrl = Get-OpenMetadataBaseUrl -Value $BaseUrl
$token = Get-OpenMetadataToken
$pfJob = $null

try {
  $pfJob = Start-OmPortForwardIfNeeded -BaseUrl $resolvedBaseUrl

  Write-Host "Buscando servicio '$ServiceName' en OpenMetadata..."
  $service = Get-DatabaseService -ServiceName $ServiceName -BaseUrl $resolvedBaseUrl -Token $token
  $tablesBefore = Get-ServiceTableCount -ServiceName $ServiceName -BaseUrl $resolvedBaseUrl -Token $token

  $deleted = $false
  if ($null -eq $service) {
    Write-Host "Servicio '$ServiceName' no existe. No hay nada que borrar."
  } else {
    Write-Host "Borrando servicio '$ServiceName' con recursive=true y hardDelete=true..."
    Remove-DatabaseService -ServiceId $service.id -BaseUrl $resolvedBaseUrl -Token $token
    $deleted = $true
    Start-Sleep -Seconds 2
  }

  $serviceAfter = Get-DatabaseService -ServiceName $ServiceName -BaseUrl $resolvedBaseUrl -Token $token
  $tablesAfter = Get-ServiceTableCount -ServiceName $ServiceName -BaseUrl $resolvedBaseUrl -Token $token

  $summary = @{
    operation = "clear_openmetadata_postgres_source"
    service_name = $ServiceName
    service_deleted = $deleted
    service_exists_after = ($null -ne $serviceAfter)
    tables_before = $tablesBefore
    tables_after = $tablesAfter
  }
  $summary | ConvertTo-Json -Depth 6
} finally {
  Stop-OmPortForward -Job $pfJob
}
