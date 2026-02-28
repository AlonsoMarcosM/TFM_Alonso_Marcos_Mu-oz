# Despliegue local de OpenMetadata en Kubernetes (Docker Desktop + Helm)

Objetivo: levantar OpenMetadata en Kubernetes local de la forma mas simple posible (PoC para TFM).

Nota (portfolio): aunque aqui se describe Docker Desktop + Kubernetes local, la idea es mantener el despliegue lo mas portable posible para poder replicarlo en un VPS o cloud (por ejemplo, un Kubernetes ligero tipo k3s o un cluster gestionado).

## Requisitos

- Docker Desktop con Kubernetes activado
- `kubectl`
- Helm 3

## Stack desplegado en esta PoC

Desde la raiz del repo se levanta un stack ?nico:
- Kubernetes (kind): `openmetadata`, `mysql`, `opensearch`, `postgres-demo`.
- Airflow interno desactivado para simplificar (ingesta por pod temporal/CLI).

## Instalación (comandos base)

Notas:
- Passwords de ejemplo: validos para una demo/TFM (hardening = trabajo futuro).
- El stack incluye dependencias (MySQL/OpenSearch/Airflow) vía chart `openmetadata-dependencies`.

```powershell
# 1) Crear secretos (MySQL + Airflow) para el chart de dependencias
kubectl create secret generic mysql-secrets --from-literal=openmetadata-mysql-password=openmetadata_password
kubectl create secret generic airflow-secrets --from-literal=openmetadata-airflow-password=admin

# 2) Anadir repo Helm de OpenMetadata
helm repo add open-metadata https://helm.open-metadata.org/
helm repo update

# 3) Instalar dependencias (MySQL + OpenSearch; Airflow desactivado en values)
helm install openmetadata-dependencies open-metadata/openmetadata-dependencies -f k8s/openmetadata-dependencies.values.yaml

# 4) Instalar OpenMetadata (sin pipelineService interno)
helm install openmetadata open-metadata/openmetadata -f k8s/openmetadata.values.yaml

# 5) Exponer la UI localmente
kubectl port-forward deployment/openmetadata 8585:8585
```

## Alternativa automatizada (desde la raiz del repo)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

## Persistencia portable del estado OpenMetadata

Para que el estado sobreviva a `kind delete cluster` y viaje con la carpeta del proyecto:

```powershell
# 1) Exportar estado de MySQL a snapshot local
powershell -ExecutionPolicy Bypass -File .\scripts\infra\backup_openmetadata_state.ps1

# 2) (opcional) borrar cluster conservando snapshot
powershell -ExecutionPolicy Bypass -File .\scripts\infra\delete_cluster_preserve_state.ps1

# 3) recrear cluster; launch_infra restaura snapshot automaticamente si existe
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

Ruta snapshot:
- `state/openmetadata/mysql/openmetadata_db.sql`

## Uso practico de Helm en este repositorio

Si `helm` no esta en PATH, usa el wrapper del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 ls -A
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 get values openmetadata-dependencies
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 get values openmetadata
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 upgrade --install openmetadata-dependencies open-metadata/openmetadata-dependencies -f k8s/openmetadata-dependencies.values.yaml
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 upgrade --install openmetadata open-metadata/openmetadata -f k8s/openmetadata.values.yaml
```

## Acceso

- UI: `http://localhost:8585`
- Credenciales por defecto (segun guia oficial): `admin@open-metadata.org` / `admin`

## Comprobaciones rapidas

```powershell
kubectl get pods
kubectl get svc
kubectl logs deployment/openmetadata --tail=100
```
