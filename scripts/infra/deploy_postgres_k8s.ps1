param(
  [string]$Namespace = "default",
  [string]$AppName = "postgres-demo",
  [string]$DbUser = "om_demo",
  [string]$DbPassword = "om_demo",
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

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

Require-Command "kubectl"

$sqlPath = Join-Path $repoRoot "sql\opendata_demo_init.sql"
if (-not (Test-Path $sqlPath)) {
  throw "No se encontro script SQL de inicializacion: $sqlPath"
}

Write-Host "Aplicando ConfigMap con SQL de inicializacion..."
kubectl create configmap "$AppName-init" `
  --namespace $Namespace `
  --from-file=001_init.sql=$sqlPath `
  --dry-run=client -o yaml | kubectl apply -f -

$manifest = @"
apiVersion: v1
kind: Service
metadata:
  name: $AppName
  namespace: $Namespace
spec:
  selector:
    app: $AppName
  ports:
  - name: postgres
    port: 5432
    targetPort: 5432
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $AppName
  namespace: $Namespace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $AppName
  template:
    metadata:
      labels:
        app: $AppName
    spec:
      containers:
      - name: postgres
        image: postgres:16
        env:
        - name: POSTGRES_USER
          value: "$DbUser"
        - name: POSTGRES_PASSWORD
          value: "$DbPassword"
        - name: POSTGRES_DB
          value: "$DbName"
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: pgdata
          mountPath: /var/lib/postgresql/data
        - name: init
          mountPath: /docker-entrypoint-initdb.d/001_init.sql
          subPath: 001_init.sql
          readOnly: true
      volumes:
      - name: pgdata
        emptyDir: {}
      - name: init
        configMap:
          name: $AppName-init
"@

$tmpManifest = Join-Path $env:TEMP "postgres_demo_k8s.yaml"
Set-Content -Path $tmpManifest -Value $manifest -Encoding ascii
kubectl apply -f $tmpManifest | Out-Null

Write-Host "Esperando a que PostgreSQL este listo..."
kubectl rollout status "deployment/$AppName" -n $Namespace --timeout=180s | Out-Null
kubectl wait --for=condition=Ready "pod" -l "app=$AppName" -n $Namespace --timeout=180s | Out-Null

Write-Host "PostgreSQL disponible en: $AppName.$Namespace.svc.cluster.local:5432"
