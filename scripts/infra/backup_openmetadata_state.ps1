param(
  [string]$Namespace = "default",
  [string]$DbUser = "openmetadata_user",
  [string]$DbPassword = "openmetadata_password",
  [string]$DbName = "openmetadata_db",
  [string]$SnapshotPath = ""
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

$snapshotDir = Split-Path -Parent $SnapshotPath
New-Item -ItemType Directory -Path $snapshotDir -Force | Out-Null

Write-Host "Esperando MySQL (statefulset/mysql) ..."
kubectl rollout status statefulset/mysql -n $Namespace --timeout=180s | Out-Null

Write-Host "Generando snapshot SQL en: $SnapshotPath"
# `--no-tablespaces` evita privilegio PROCESS en MySQL gestionado por chart.
$dumpCmd = "MYSQL_PWD='$DbPassword' mysqldump --single-transaction --quick --routines --triggers --no-tablespaces -u '$DbUser' '$DbName'"
kubectl exec -n $Namespace statefulset/mysql -- sh -c $dumpCmd | Out-File -FilePath $SnapshotPath -Encoding utf8
if ($LASTEXITCODE -ne 0) {
  throw "mysqldump fallo con codigo $LASTEXITCODE"
}

$size = (Get-Item $SnapshotPath).Length
Write-Host "Snapshot completado. Bytes: $size"
