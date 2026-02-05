# A01 - Prerrequisitos

## Ubicacion de trabajo

Todas las acciones se ejecutan desde:

`F:\DISCO DURO PORTABLE\INGENIERIA\MASTER\TFM\TFM_Alonso_Marcos_Mu-oz`

## Requisitos de software

- Docker Desktop (con Kubernetes si se usa ese modo)
- `docker`
- `kubectl`
- `kind` (opcion recomendada para cluster local reproducible)
- Helm 3 (el script descarga una copia local si no esta disponible en PATH)
- Python 3.10+ (para `tfm_ingestor`)

## Comprobacion rapida

```powershell
docker --version
kubectl version --client
kind --version
python --version
```

## Nota sobre Helm

OpenMetadata requiere Helm 3. El repositorio incluye soporte para usar:
- Helm 3 en PATH, o
- Helm 3 local descargado en `.tools/helm-v3.14.4/windows-amd64/helm.exe`.
