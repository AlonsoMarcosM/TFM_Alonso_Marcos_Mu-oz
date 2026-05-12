# A02 - Despliegue de infraestructura desde el repositorio

Este anexo deja toda la infraestructura arrancada desde un único punto de entrada.

Para una explicación conceptual de qué son Docker, Kind, Kubernetes, Helm, OpenMetadata, MySQL, OpenSearch y `postgres-demo` en esta plataforma, ver:

- `docs/openmetadata_k8s.md`

## Opción recomendada automatizada

Desde la raíz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

Qué hace el script, en orden:

1. Crea o reutiliza el clúster `kind` (`kind-tfm-om`).
2. Despliega PostgreSQL de referencia dentro de Kubernetes (`postgres-demo`).
3. Crea secretos `mysql-secrets` y `airflow-secrets`.
4. Instala `openmetadata-dependencies` con ajustes locales (`k8s/openmetadata-dependencies.values.yaml`).
5. Restaura automáticamente el snapshot de estado si existe en `state/openmetadata/mysql/openmetadata_db.sql`.
6. Instala `openmetadata`.

Stack final esperado:

- Docker: `tfm-om-control-plane`
- Kubernetes: `postgres-demo`, `mysql`, `opensearch`, `openmetadata`
- Helm: releases `openmetadata-dependencies` y `openmetadata`

Lectura simple:

```text
Docker ejecuta el nodo Kind.
Kind proporciona Kubernetes local.
Kubernetes ejecuta los pods.
Helm instala OpenMetadata y sus dependencias.
El repo automatiza todo con scripts versionados.
```

## Persistencia de estado

El estado funcional de OpenMetadata, por ejemplo tags, dominios, owners y metadatos, se guarda en MySQL.

Para llevarte ese estado con la carpeta del proyecto:

- Snapshot SQL local:
  - `state/openmetadata/mysql/openmetadata_db.sql`

Comandos:

```powershell
# Guardar estado actual en carpeta del proyecto
powershell -ExecutionPolicy Bypass -File .\scripts\infra\backup_openmetadata_state.ps1

# Borrar clúster conservando snapshot
powershell -ExecutionPolicy Bypass -File .\scripts\infra\delete_cluster_preserve_state.ps1

# Levantar de nuevo y restaurar automáticamente si existe snapshot
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

Notas:

- `launch_infra.ps1` restaura automáticamente el snapshot si existe.
- Puedes desactivar restauración con `-SkipStateRestore`.
- `state/` está en `.gitignore` y no se sube al remoto.

## Réplica en otro portátil

Caso esperado: clonar o copiar el repositorio en otro equipo y levantar la plataforma desde cero.

Pasos mínimos:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\check_prereqs.ps1 -Strict
python -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\status_infra.ps1
```

Si falta Helm 3 en el equipo, el repositorio puede descargar una copia local en `.tools/`.

Si se quiere conservar el estado funcional de OpenMetadata entre equipos, copiar también el snapshot local:

```text
state/openmetadata/mysql/openmetadata_db.sql
```

Este snapshot no se sube a Git porque puede contener estado local del entorno.

## Exposición de OpenMetadata UI

En una terminal aparte:

```powershell
kubectl port-forward svc/openmetadata 8585:8585
```

Si se corta al reiniciarse el pod, usa auto-reconexión:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\port_forward_openmetadata.ps1
```

Acceso:

- URL: `http://localhost:8585`
- Usuario: `admin@open-metadata.org`
- Password: `admin`

## Verificación de estado

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\status_infra.ps1
```

## Helm desde el repo

Aunque Helm no esté en `PATH`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 ls -A
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 get values openmetadata
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 get values openmetadata-dependencies
```

Estado validado en este entorno el 4 de febrero de 2026:

- `openmetadata` en estado `deployed`
- `openmetadata-dependencies` en estado `deployed`
- pods principales en `Running`

## Comentario para VPS/cloud

El flujo es portable: los mismos charts Helm y la misma lógica aplican en un Kubernetes de VPS/cloud, por ejemplo k3s en un VPS o un clúster gestionado.

Cambian principalmente:

- storage class;
- recursos CPU/memoria;
- configuración de red;
- ingress o balanceador;
- secretos;
- backups;
- observabilidad.

En una empresa no se usaría Kind como entorno principal. Kind se usa aquí porque permite ejecutar Kubernetes + Helm de forma local, barata y reproducible.
