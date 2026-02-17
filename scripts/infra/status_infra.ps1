$ErrorActionPreference = "Stop"

Write-Host "Contexto actual:"
kubectl config current-context

Write-Host "`nReleases Helm:"
$helmCmd = Get-Command helm -ErrorAction SilentlyContinue
if ($helmCmd) {
  # Helm v4 no soporta `-a` (era shorthand antiguo). Por defecto lista releases en cualquier estado.
  & $helmCmd.Source ls -A
} else {
  $localHelm = Join-Path (Resolve-Path ".").Path ".tools\helm-v3.14.4\windows-amd64\helm.exe"
  if (Test-Path $localHelm) {
    & $localHelm ls -A
  } else {
    Write-Host "Helm no encontrado en PATH ni en .tools."
  }
}

Write-Host "`nPods:"
kubectl get pods -o wide

Write-Host "`nServicios:"
kubectl get svc

Write-Host "`nPostgreSQL en Kubernetes:"
kubectl get svc postgres-demo --ignore-not-found
kubectl get pods -l app=postgres-demo --ignore-not-found
