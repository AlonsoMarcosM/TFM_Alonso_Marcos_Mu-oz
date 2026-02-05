param(
  [string]$ClusterName = "tfm-om",
  [switch]$SkipOpenMetadata
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Resolve-Helm3 {
  $localHelm = Join-Path (Resolve-RepoRoot) ".tools\helm-v3.14.4\windows-amd64\helm.exe"

  $helmCmd = Get-Command helm -ErrorAction SilentlyContinue
  if ($helmCmd) {
    $ver = (& $helmCmd.Source version --short) 2>$null
    if ($ver -match "v3\.") {
      return $helmCmd.Source
    }
  }

  if (Test-Path $localHelm) {
    return $localHelm
  }

  Write-Host "Helm 3 no encontrado en PATH. Descargando version local..."
  $toolsDir = Join-Path (Resolve-RepoRoot) ".tools"
  New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
  $zipPath = Join-Path $toolsDir "helm-v3.14.4-windows-amd64.zip"
  Invoke-WebRequest -Uri "https://get.helm.sh/helm-v3.14.4-windows-amd64.zip" -OutFile $zipPath
  Expand-Archive -Path $zipPath -DestinationPath (Join-Path $toolsDir "helm-v3.14.4") -Force
  return $localHelm
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

  $fromWinget = Get-ChildItem `
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" `
    -Recurse -Filter kind.exe -ErrorAction SilentlyContinue | Select-Object -First 1

  if ($fromWinget) {
    return $fromWinget.FullName
  }

  throw "kind no encontrado. Instalar con: winget install --id Kubernetes.kind -e"
}

function Get-ReleaseStatus([string]$helmPath, [string]$releaseName) {
  $json = & $helmPath ls -a --filter "^$releaseName$" -o json
  if (-not $json) { return $null }
  $items = $json | ConvertFrom-Json
  if (-not $items -or $items.Count -eq 0) { return $null }
  return $items[0].status
}

function Ensure-NoPendingRelease([string]$helmPath, [string]$releaseName) {
  $status = Get-ReleaseStatus -helmPath $helmPath -releaseName $releaseName
  if ($null -eq $status) { return }

  if ($status -like "pending-*") {
    Write-Host "Release '$releaseName' en estado $status. Haciendo uninstall para recuperar estado..."
    & $helmPath uninstall $releaseName
  }
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

Require-Command "docker"
Require-Command "kubectl"
$helm = Resolve-Helm3
$kind = Resolve-Kind

Write-Host "Repositorio: $repoRoot"
Write-Host "Helm usado: $helm"
Write-Host "kind usado: $kind"

Write-Host "`n[1/5] Asegurando cluster kind '$ClusterName'..."
$clusters = & $kind get clusters
if ($clusters -notcontains $ClusterName) {
  & $kind create cluster --name $ClusterName --wait 5m
}
$ctx = "kind-$ClusterName"
kubectl config use-context $ctx | Out-Null

Write-Host "`n[2/5] Provisionando PostgreSQL en Kubernetes..."
# Limpieza defensiva de un posible contenedor legado fuera de k8s.
$legacy = docker ps -a --filter "name=^tfm-postgres$" --format "{{.Names}}"
if ($legacy -and $legacy.Trim().Length -gt 0) {
  docker rm -f tfm-postgres *> $null
}
powershell -ExecutionPolicy Bypass -File ".\scripts\infra\deploy_postgres_k8s.ps1"

Write-Host "`n[3/5] Creando secretos de OpenMetadata..."
kubectl create secret generic mysql-secrets `
  --from-literal=openmetadata-mysql-password=openmetadata_password `
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic airflow-secrets `
  --from-literal=openmetadata-airflow-password=admin `
  --dry-run=client -o yaml | kubectl apply -f -

Write-Host "`n[4/5] Instalando dependencias OpenMetadata (Helm)..."
& $helm repo add open-metadata https://helm.open-metadata.org/ 2>$null
& $helm repo update
Ensure-NoPendingRelease -helmPath $helm -releaseName "openmetadata-dependencies"
& $helm upgrade --install openmetadata-dependencies open-metadata/openmetadata-dependencies `
  -f "k8s/openmetadata-dependencies.values.yaml" `
  --wait --timeout 25m

if (-not $SkipOpenMetadata) {
  Write-Host "`n[5/5] Instalando OpenMetadata (Helm)..."
  Ensure-NoPendingRelease -helmPath $helm -releaseName "openmetadata"
  & $helm upgrade --install openmetadata open-metadata/openmetadata `
    -f "k8s/openmetadata.values.yaml" `
    --wait --timeout 20m
}

Write-Host "`nEstado de pods:"
kubectl get pods -o wide

Write-Host "`nSiguiente comando (nueva terminal):"
Write-Host "kubectl port-forward deployment/openmetadata 8585:8585"
