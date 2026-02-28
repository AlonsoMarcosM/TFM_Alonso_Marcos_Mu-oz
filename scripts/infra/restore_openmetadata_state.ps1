param(
  [string]$Namespace = "default",
  [string]$DbUser = "openmetadata_user",
  [string]$DbPassword = "openmetadata_password",
  [string]$DbName = "openmetadata_db",
  [string]$SnapshotPath = "",
  [switch]$AllowMissing
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

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot
Require-Command "kubectl"

if (-not $SnapshotPath) {
  $SnapshotPath = Join-Path $repoRoot "state\openmetadata\mysql\openmetadata_db.sql"
}

if (-not (Test-Path $SnapshotPath)) {
  if ($AllowMissing) {
    Write-Host "No existe snapshot en $SnapshotPath (skip)."
    exit 0
  }
  throw "No existe snapshot SQL: $SnapshotPath"
}

Write-Host "Esperando MySQL (statefulset/mysql) ..."
kubectl rollout status statefulset/mysql -n $Namespace --timeout=180s | Out-Null

Write-Host "Restaurando estado desde snapshot: $SnapshotPath"
$importCmd = "MYSQL_PWD='$DbPassword' mysql -u '$DbUser' '$DbName'"
Get-Content -Path $SnapshotPath -Raw | kubectl exec -i -n $Namespace statefulset/mysql -- sh -c $importCmd | Out-Null

Write-Host "Restauracion completada."
