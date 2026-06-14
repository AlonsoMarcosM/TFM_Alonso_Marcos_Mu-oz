# A01 - Prerrequisitos

## Ubicación de trabajo

Todas las acciones se ejecutan desde la raíz del repositorio.

Ejemplo del entorno actual:

```text
F:\DISCO DURO PORTABLE\INGENIERIA\MASTER\TFM\TFM_Alonso_Marcos_Mu-oz
```

## Requisitos de software

- Docker Desktop
- `docker`
- `kubectl`
- `kind`
- Helm 3
- Python 3.10+

Kind es la opción recomendada para el clúster local reproducible. Tanto **Helm 3** como **kind** pueden estar instalados en `PATH` o ser **descargados automáticamente** por los scripts del repo en `.tools/` (`launch_infra.ps1` resuelve y, si faltan, descarga `helm.exe` y `kind.exe`). Por eso, en un equipo con solo Docker Desktop + Python, basta con tener `kubectl`: el resto se autoprovisiona. `check_prereqs.ps1` reconoce las copias locales en `.tools/`, por lo que la comprobación `-Strict` pasa aunque Helm/kind no estén en el `PATH` del sistema.

### Consola web (opcional)

La consola web (`web/`) es la ruta equivalente al CLI y no es necesaria para la suite de validación del núcleo. Si se quiere levantar o validar:

- **Node.js ≥ 20.19** (recomendado **22 LTS**). Versiones anteriores (p. ej. 20.18) no cumplen los `engines` de las herramientas web actuales (Next.js 16 y `vitest` 4 / `rolldown`), que exigen `^20.19.0 || >=22.12.0`. Igual que Helm/kind, puede usarse una copia portable en `.tools/node/` sin tocar el Node del sistema.
- **pnpm** (gestor Node canónico) provisionado con **corepack** (incluido en Node): `corepack prepare pnpm@10 --activate`.

Notas de entorno reproducible para `web/`:

- Si corepack falla al verificar firmas (`Cannot find matching keyid`, bug de claves caducadas en el corepack que acompaña a Node 20.18), exportar `COREPACK_INTEGRITY_KEYS=0`.
- En instalaciones no interactivas (sin TTY), `pnpm install` puede pedir confirmación para purgar `node_modules`; exportar `CI=true` para que continúe.
- Comandos: `pnpm install`, `pnpm test` (vitest), `pnpm build` (Next.js), `pnpm dev` (puerto 3000).

## Versión de OpenMetadata

La versión de OpenMetadata desplegada y validada en este entorno es **1.12.9**, instalada con los charts oficiales de Helm. Puede comprobarse en cualquier momento contra la instancia viva:

```powershell
Invoke-RestMethod http://localhost:8585/api/v1/system/version
```

La lógica de gobierno usa entidades estables de la API REST (servicios, bases de datos, esquemas, tablas, custom properties y tags), por lo que es compatible con la rama 1.12.x y versiones próximas que conserven esas entidades.

## Comprobación rápida recomendada

Comando canónico del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\check_prereqs.ps1 -Strict
```

El script verifica los comandos necesarios y deja informe JSON en:

```text
tmp_pytest/prereqs_report.json
```

## Comprobación manual alternativa

```powershell
docker --version
kubectl version --client
kind --version
helm version --short
python --version
```

## Si se replica en un portátil nuevo

La ruta más simple es:

1. Instalar Docker Desktop.
2. Instalar `kubectl`.
3. Instalar `kind`.
4. Instalar Python 3.10 o superior.
5. Ejecutar `check_prereqs.ps1 -Strict`.
6. Instalar dependencias Python.
7. Ejecutar `launch_infra.ps1`.

Comandos desde la raíz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\check_prereqs.ps1 -Strict
python -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

Si se copia también el estado local de OpenMetadata, conservar:

```text
state/openmetadata/mysql/openmetadata_db.sql
```

Ese snapshot permite reconstruir el clúster y restaurar tags, custom properties y metadatos ya aplicados en OpenMetadata.

## Instalación Python del repositorio

Desde la raíz del repo:

```powershell
python -m pip install -r requirements-dev.txt
```

Si solo quieres las dependencias de ejecución:

```powershell
python -m pip install -r requirements.txt
```

## Nota sobre Helm

OpenMetadata requiere Helm 3. El repositorio incluye soporte para usar:

- Helm 3 en `PATH`;
- Helm 3 local descargado en `.tools/helm-v3.14.4/windows-amd64/helm.exe`.

Wrapper del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 version
```
