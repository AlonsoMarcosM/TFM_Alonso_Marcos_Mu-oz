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

Kind es la opción recomendada para el clúster local reproducible. Helm 3 puede estar instalado en `PATH` o ser descargado automáticamente por los scripts del repo en `.tools/`.

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
