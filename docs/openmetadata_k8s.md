# Despliegue local de OpenMetadata en Kubernetes (Docker Desktop + Helm)

Objetivo: levantar OpenMetadata en Kubernetes local de la forma mas simple posible (PoC para TFM).

Nota (portfolio): aunque aqui se describe Docker Desktop + Kubernetes local, la idea es mantener el despliegue lo mas portable posible para poder replicarlo en un VPS o cloud (por ejemplo, un Kubernetes ligero tipo k3s o un cluster gestionado).

## Requisitos

- Docker Desktop con Kubernetes activado
- `kubectl`
- Helm 3

## Instalacion (comandos base)

Notas:
- Passwords de ejemplo: validos para una demo/TFM (hardening = trabajo futuro).
- El stack incluye dependencias (MySQL/OpenSearch/Airflow) via chart `openmetadata-dependencies`.

```powershell
# 1) Crear secretos (MySQL + Airflow) para el chart de dependencias
kubectl create secret generic mysql-secrets --from-literal=openmetadata-mysql-password=openmetadata_password
kubectl create secret generic airflow-secrets --from-literal=openmetadata-airflow-password=admin

# 2) Anadir repo Helm de OpenMetadata
helm repo add open-metadata https://helm.open-metadata.org/
helm repo update

# 3) Instalar dependencias (incluye Airflow)
helm install openmetadata-dependencies open-metadata/openmetadata-dependencies

# 4) Instalar OpenMetadata
helm install openmetadata open-metadata/openmetadata

# 5) Exponer la UI localmente
kubectl port-forward deployment/openmetadata 8585:8585
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
