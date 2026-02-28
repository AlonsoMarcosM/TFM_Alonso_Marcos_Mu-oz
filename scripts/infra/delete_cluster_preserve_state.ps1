param(
  [string]$ClusterName = "tfm-om",
  [switch]$SkipBackup
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Resolve-Kind {
  $kindCmd = Get-Command kind -ErrorAction SilentlyContinue
  if ($kindCmd) {
    return $kindCmd.Source
  }
  throw "kind no encontrado en PATH."
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot
$kind = Resolve-Kind

if (-not $SkipBackup) {
  Write-Host "[1/2] Backup de estado OpenMetadata a carpeta del proyecto..."
  powershell -ExecutionPolicy Bypass -File ".\scripts\infra\backup_openmetadata_state.ps1"
}

Write-Host "[2/2] Eliminando cluster kind '$ClusterName'..."
& $kind delete cluster --name $ClusterName
Write-Host "Cluster eliminado. Snapshot local disponible en state\\openmetadata\\mysql\\openmetadata_db.sql"
