param(
  [string]$ClusterName = "tfm-om",
  [switch]$SkipBackup,
  [switch]$RunFullFlow,
  [switch]$SkipPipInstall
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Require-Command([string]$name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "No se encuentra el comando requerido: $name"
  }
}

function Resolve-Kind {
  $kindCmd = Get-Command kind -ErrorAction SilentlyContinue
  if ($kindCmd) {
    return $kindCmd.Source
  }
  throw "kind no encontrado en PATH."
}

function Archive-Snapshot {
  param([string]$RepoRoot)

  $snapshot = Join-Path $RepoRoot "state\openmetadata\mysql\openmetadata_db.sql"
  if (-not (Test-Path -LiteralPath $snapshot)) {
    Write-Host "No hay snapshot activo que apartar: $snapshot"
    return
  }

  $archiveDir = Join-Path $RepoRoot "state\openmetadata\mysql\archive"
  New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $target = Join-Path $archiveDir "openmetadata_db_$stamp.sql"
  Move-Item -LiteralPath $snapshot -Destination $target -Force
  Write-Host "Snapshot anterior archivado para evitar restauracion automatica: $target"
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

Require-Command "kind"
Require-Command "kubectl"

$kind = Resolve-Kind
$clusters = & $kind get clusters
$clusterExists = $clusters -contains $ClusterName

if ($clusterExists -and -not $SkipBackup) {
  Write-Host "[1/4] Backup previo del estado OpenMetadata..."
  powershell -ExecutionPolicy Bypass -File ".\scripts\infra\backup_openmetadata_state.ps1"
} else {
  Write-Host "[1/4] Backup previo omitido."
}

if ($clusterExists) {
  Write-Host "[2/4] Eliminando cluster kind '$ClusterName'..."
  & $kind delete cluster --name $ClusterName
} else {
  Write-Host "[2/4] No existe cluster kind '$ClusterName'."
}

Write-Host "[3/4] Apartando snapshot para arrancar sin restaurar datos anteriores..."
Archive-Snapshot -RepoRoot $repoRoot

if ($RunFullFlow) {
  Write-Host "[4/4] Ejecutando flujo completo desde infraestructura limpia..."
  $flowArgs = @("-ExecutionPolicy", "Bypass", "-File", ".\scripts\infra\run_full_flow.ps1")
  if ($SkipPipInstall) {
    $flowArgs += "-SkipPipInstall"
  }
  powershell @flowArgs
} else {
  Write-Host "[4/4] Levantando infraestructura limpia sin restaurar snapshot..."
  powershell -ExecutionPolicy Bypass -File ".\scripts\infra\launch_infra.ps1" -SkipStateRestore
}
