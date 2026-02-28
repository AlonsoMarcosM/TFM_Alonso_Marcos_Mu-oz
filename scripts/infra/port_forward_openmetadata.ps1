param(
  [string]$Namespace = "default",
  [int]$LocalPort = 8585,
  [int]$RemotePort = 8585,
  [int]$RetrySeconds = 2
)

$ErrorActionPreference = "Continue"

Write-Host "Iniciando port-forward con auto-reconexion..."
Write-Host "Destino: svc/openmetadata ($Namespace)"
Write-Host "URL: http://127.0.0.1:$LocalPort"
Write-Host "Pulsa Ctrl+C para terminar."

while ($true) {
  try {
    kubectl -n $Namespace port-forward svc/openmetadata "$LocalPort`:$RemotePort"
  } catch {
    Write-Host "Port-forward interrumpido: $($_.Exception.Message)"
  }

  Write-Host "Reintentando en $RetrySeconds s..."
  Start-Sleep -Seconds $RetrySeconds
}

