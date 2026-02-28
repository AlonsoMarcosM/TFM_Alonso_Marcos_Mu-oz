# A02 - Despliegue de infraestructura desde el repositorio

Este anexo deja toda la infraestructura arrancada desde un ?nico punto de entrada.

## Opcion recomendada (automatizada)

Desde la raiz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

Que hace el script, en orden:
1. Despliega PostgreSQL dummy dentro de Kubernetes (`postgres-demo`)
2. Crea/usa cluster `kind` (`kind-tfm-om`)
3. Crea secretos `mysql-secrets` y `airflow-secrets`
4. Instala `openmetadata-dependencies` con overrides locales (`k8s/openmetadata-dependencies.values.yaml`)
5. Instala `openmetadata`

Stack final esperado:
- Docker: `tfm-om-control-plane`
- Kubernetes: `postgres-demo`, `mysql`, `opensearch`, `openmetadata`

## Persistencia de estado (sobrevive a `kind delete cluster`)

El estado funcional de OpenMetadata (tags, dominios, owners, metadatos) se guarda en MySQL.
Para llevarte ese estado con la carpeta del proyecto:

- Snapshot SQL local (ruta relativa al repo):
  - `state/openmetadata/mysql/openmetadata_db.sql`

Comandos:

```powershell
# Guardar estado actual en carpeta del proyecto
powershell -ExecutionPolicy Bypass -File .\scripts\infra\backup_openmetadata_state.ps1

# Borrar cluster conservando snapshot
powershell -ExecutionPolicy Bypass -File .\scripts\infra\delete_cluster_preserve_state.ps1

# Levantar de nuevo y restaurar automaticamente si existe snapshot
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

Notas:
- `launch_infra.ps1` restaura automáticamente el snapshot si existe.
- Puedes desactivar restauracion con `-SkipStateRestore`.
- `state/` esta en `.gitignore` (no se sube al remoto).

## Exposicion de OpenMetadata UI

En una terminal aparte:

```powershell
kubectl port-forward svc/openmetadata 8585:8585
```

Si se corta al reiniciarse el pod, usa auto-reconexion:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\port_forward_openmetadata.ps1
```

Acceso:
- URL: `http://localhost:8585`
- Usuario: `admin@open-metadata.org`
- Password: `admin`

## Verificacion de estado

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\status_infra.ps1
```

## Helm desde el repo (aunque no este en PATH)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 ls -A
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 get values openmetadata
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 get values openmetadata-dependencies
```

Estado validado en este entorno (04/02/2026):
- `openmetadata` en estado `deployed`
- `openmetadata-dependencies` en estado `deployed`
- Pods principales en `Running`

## Comentario para VPS/cloud

El flujo es portable: los mismos charts Helm y la misma lógica aplican en un Kubernetes de VPS/cloud (k3s o gestionado).  
Cambian principalmente: storage class, recursos y configuración de red/ingress.
