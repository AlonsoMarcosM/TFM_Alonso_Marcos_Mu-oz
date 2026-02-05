param(
  [string]$ServiceName = "postgres_demo_service",
  [string]$DbUser = "om_demo",
  [string]$DbPassword = "om_demo",
  [string]$DbHostPort = "",
  [string]$DbName = "opendata_demo"
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

function New-OmToken {
  param([string]$RepoRoot)
  $token = python (Join-Path $RepoRoot "scripts\infra\generate_om_jwt.py") --ttl-hours 2
  if (-not $token) {
    throw "No se pudo generar token JWT para OpenMetadata."
  }
  return $token.Trim()
}

function Start-OmPortForward {
  $job = Start-Job -ScriptBlock {
    kubectl port-forward deployment/openmetadata 8585:8585
  }
  Start-Sleep -Seconds 3
  return $job
}

function Stop-OmPortForward {
  param($Job)
  if ($null -ne $Job) {
    Stop-Job $Job -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $Job -Force -ErrorAction SilentlyContinue | Out-Null
  }
}

function Invoke-OmApi {
  param(
    [string]$Method,
    [string]$Path,
    [string]$Token,
    [object]$Body = $null
  )
  $url = "http://localhost:8585/api/v1$Path"
  $headers = @{ Authorization = "Bearer $Token" }
  if ($null -eq $Body) {
    return Invoke-RestMethod -Uri $url -Headers $headers -Method $Method
  }
  $json = $Body | ConvertTo-Json -Depth 20
  return Invoke-RestMethod -Uri $url -Headers $headers -Method $Method -Body $json -ContentType "application/json"
}

function Ensure-DatabaseService {
  param(
    [string]$Token,
    [string]$ServiceName,
    [string]$DbUser,
    [string]$DbPassword,
    [string]$DbHostPort,
    [string]$DbName
  )

  try {
    Invoke-OmApi -Method "GET" -Path "/services/databaseServices/name/$ServiceName" -Token $Token | Out-Null
    Write-Host "Servicio '$ServiceName' ya existe en OpenMetadata."
    return
  } catch {
    $status = $null
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
      $status = [int]$_.Exception.Response.StatusCode.value__
    }
    if ($status -ne 404) {
      throw
    }
  }

  $body = @{
    name = $ServiceName
    serviceType = "Postgres"
    connection = @{
      config = @{
        type = "Postgres"
        scheme = "postgresql+psycopg2"
        username = $DbUser
        authType = @{ password = $DbPassword }
        hostPort = $DbHostPort
        database = $DbName
      }
    }
  }

  Invoke-OmApi -Method "POST" -Path "/services/databaseServices" -Token $Token -Body $body | Out-Null
  Write-Host "Servicio '$ServiceName' creado en OpenMetadata."
}

function Resolve-IngestionImage {
  $serverImage = kubectl get deployment openmetadata -o jsonpath="{.spec.template.spec.containers[0].image}"
  if ($LASTEXITCODE -ne 0 -or -not $serverImage) {
    return "docker.getcollate.io/openmetadata/ingestion:1.11.8"
  }
  if ($serverImage -match "^(.*)/server:([^:]+)$") {
    return "$($matches[1])/ingestion:$($matches[2])"
  }
  return "docker.getcollate.io/openmetadata/ingestion:1.11.8"
}

function Run-IngestionPod {
  param(
    [string]$RepoRoot,
    [string]$ServiceName,
    [string]$DbUser,
    [string]$DbPassword,
    [string]$DbHostPort,
    [string]$DbName,
    [string]$Token
  )

  $ingestionImage = Resolve-IngestionImage
  Write-Host "Imagen de ingesta: $ingestionImage"

  $cfg = @"
source:
  type: postgres
  serviceName: $ServiceName
  serviceConnection:
    config:
      type: Postgres
      scheme: postgresql+psycopg2
      username: $DbUser
      authType:
        password: $DbPassword
      hostPort: $DbHostPort
      database: $DbName
  sourceConfig:
    config:
      type: DatabaseMetadata
      markDeletedTables: false
      includeTables: true
      includeViews: true
      databaseFilterPattern:
        includes:
          - $DbName
      schemaFilterPattern:
        includes:
          - bronze
          - silver
          - gold
sink:
  type: metadata-rest
  config: {}
workflowConfig:
  loggerLevel: INFO
  openMetadataServerConfig:
    hostPort: http://openmetadata:8585/api
    authProvider: openmetadata
    securityConfig:
      jwtToken: "$Token"
"@

  $tmpCfg = Join-Path $env:TEMP "om_ingestion_tfm.yaml"
  Set-Content -Path $tmpCfg -Value $cfg -Encoding ascii
  kubectl create configmap om-postgres-ingest-config --from-file=ingestion.yaml=$tmpCfg --dry-run=client -o yaml | kubectl apply -f -

  $podYaml = @"
apiVersion: v1
kind: Pod
metadata:
  name: om-postgres-ingest
spec:
  restartPolicy: Never
  containers:
  - name: om-postgres-ingest
    image: $ingestionImage
    command: ["sh","-c","metadata ingest -c /config/ingestion.yaml"]
    volumeMounts:
    - name: cfg
      mountPath: /config
  volumes:
  - name: cfg
    configMap:
      name: om-postgres-ingest-config
"@

  $tmpPod = Join-Path $env:TEMP "om_ingestion_tfm_pod.yaml"
  Set-Content -Path $tmpPod -Value $podYaml -Encoding ascii

  kubectl delete pod om-postgres-ingest --ignore-not-found | Out-Null
  kubectl apply -f $tmpPod | Out-Null

  kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/om-postgres-ingest --timeout=600s | Out-Null
  if ($LASTEXITCODE -ne 0) {
    kubectl logs om-postgres-ingest --tail=200
    throw "La ingesta tecnica no termino en estado Succeeded."
  }

  Write-Host "Ingesta tecnica completada."
  kubectl logs om-postgres-ingest --tail=120

  kubectl delete pod om-postgres-ingest --ignore-not-found | Out-Null
  kubectl delete configmap om-postgres-ingest-config --ignore-not-found | Out-Null
}

function Print-TableSummary {
  param([string]$Token, [string]$ServiceName)

  $tables = Invoke-OmApi -Method "GET" -Path "/tables?limit=1000" -Token $Token
  $items = @($tables.data | Where-Object { $_.fullyQualifiedName -like "$ServiceName.*" })
  Write-Host "Tablas detectadas para '$ServiceName': $($items.Count)"
  $items | Select-Object -First 6 | ForEach-Object { Write-Host " - $($_.fullyQualifiedName)" }
}

function Resolve-DbHostPort {
  param([string]$Value)

  if ($Value -and $Value.Trim().Length -gt 0) {
    return $Value.Trim()
  }

  $svc = kubectl get svc postgres-demo -o name --ignore-not-found
  if ($svc -and $svc.Trim().Length -gt 0) {
    return "postgres-demo.default.svc.cluster.local:5432"
  }

  throw "No existe el servicio postgres-demo en Kubernetes. Ejecuta launch_infra.ps1 primero."
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

Require-Command "kubectl"
Require-Command "python"

$DbHostPort = Resolve-DbHostPort -Value $DbHostPort
Write-Host "DB host:port seleccionado: $DbHostPort"

Write-Host "[1/3] Generando token de OpenMetadata..."
$token = New-OmToken -RepoRoot $repoRoot

$pfJob = $null
try {
  Write-Host "[2/3] Verificando/creando servicio Postgres en OpenMetadata..."
  $pfJob = Start-OmPortForward
  Ensure-DatabaseService `
    -Token $token `
    -ServiceName $ServiceName `
    -DbUser $DbUser `
    -DbPassword $DbPassword `
    -DbHostPort $DbHostPort `
    -DbName $DbName
  Stop-OmPortForward -Job $pfJob
  $pfJob = $null

  Write-Host "[3/3] Ejecutando ingesta tecnica desde pod temporal..."
  Run-IngestionPod `
    -RepoRoot $repoRoot `
    -ServiceName $ServiceName `
    -DbUser $DbUser `
    -DbPassword $DbPassword `
    -DbHostPort $DbHostPort `
    -DbName $DbName `
    -Token $token

  $pfJob = Start-OmPortForward
  Print-TableSummary -Token $token -ServiceName $ServiceName
} finally {
  Stop-OmPortForward -Job $pfJob
}
