$ErrorActionPreference = "Stop"

Write-Host "Contexto actual:"
kubectl config current-context

Write-Host "`nReleases Helm:"
$helmCmd = Get-Command helm -ErrorAction SilentlyContinue
if ($helmCmd) {
  & $helmCmd.Source ls -a
} else {
  $localHelm = Join-Path (Resolve-Path ".").Path ".tools\helm-v3.14.4\windows-amd64\helm.exe"
  if (Test-Path $localHelm) {
    & $localHelm ls -a
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
