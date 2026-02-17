# MVP GitHub Projects para planificacion del TFM

Objetivo: sustituir Microsoft Planner por un flujo reproducible en GitHub Projects (v2), creado por codigo.

Este MVP crea de forma idempotente:
- Project (v2) del TFM
- campos single-select (`Estado TFM`, `Fase TFM`, `Tipo TFM`)
- labels por tipo y fase
- milestones por fase
- issues base del roadmap (extraidas de la documentacion del repo)
- alta de issues en el Project y asignacion de campos
- enlace del Project al repositorio para que aparezca en `/<owner>/<repo>/projects`

El roadmap se toma del orden canonico definido en:
- `docs/planificacion_kanban.md`
- fases: `01_Planificacion -> 02_Modelo_DCAT-AP -> 03_OpenMetadata_Config -> 04_Pipeline_Ingesta -> 05_Validacion -> 06_Memoria`

## Archivos del MVP

- Script: `scripts/planning/bootstrap_github_project.py`
- Config declarativa: `scripts/planning/github_project_mvp.json`

## Prerrequisitos

- Python 3.10+
- Repositorio en GitHub con permisos para crear issues/milestones/projects
- Token con permisos (elige 1 enfoque):
  - PAT classic: scopes `repo`, `project`, `read:user` (y `read:org` solo si `--owner` es una organizacion)
  - Fine-grained PAT:
    - Account permissions: `Projects` = Read and write
    - Repository permissions (para el repo objetivo): `Issues` = Read and write, `Metadata` = Read-only

Puedes usar `GITHUB_TOKEN` o `GH_TOKEN`.

## 1) Dry-run local (sin tocar GitHub)

Desde la raiz del repo:

```powershell
python .\scripts\planning\bootstrap_github_project.py
```

Salida esperada:
- JSON con conteos
- preview de labels/milestones/issues
- campos del proyecto que se crearian

## 2) Aplicar en GitHub (creacion real)

Configura variables y ejecuta:

```powershell
$env:GITHUB_TOKEN="<TOKEN>"
$env:GITHUB_OWNER="<usuario_o_org>"
$env:GITHUB_REPO="<repositorio>"

python .\scripts\planning\bootstrap_github_project.py --apply
```

Opcional: personalizar titulo del Project.

```powershell
python .\scripts\planning\bootstrap_github_project.py --apply --project-title "TFM - Seguimiento 2026"
```

## (Opcional) Borrar todos los Projects v2 del owner

Accion destructiva. Usa solo si quieres limpiar todos los proyectos personales.

```powershell
$env:GITHUB_TOKEN="<TOKEN>"
python .\scripts\planning\bootstrap_github_project.py --delete-projects --confirm DELETE_ALL_PROJECTS --owner AlonsoMarcosM
```

## (Opcional) Borrar milestones antiguas antes de crear el Project

Elimina milestones que no pertenecen al roadmap actual y que empiecen por `Fase `.

```powershell
$env:GITHUB_TOKEN="<TOKEN>"
python .\scripts\planning\bootstrap_github_project.py --delete-old-milestones --confirm DELETE_OLD_MILESTONES --owner AlonsoMarcosM --repo TFM_Alonso_Marcos_Mu-oz
```

Si tus milestones antiguas tienen otro prefijo:

```powershell
python .\scripts\planning\bootstrap_github_project.py --delete-old-milestones --confirm DELETE_OLD_MILESTONES --owner AlonsoMarcosM --repo TFM_Alonso_Marcos_Mu-oz --milestone-prefix "Fase ,Fase 1 -"
```

## 3) Comportamiento idempotente

Si ejecutas el script varias veces:
- no duplica labels
- no duplica milestones
- no duplica issues (compara por titulo con prefijo `[TFM]`)
- no duplica items en el Project
- vuelve a aplicar valores de campos para mantener coherencia

Nota: si cambias las opciones de un campo existente (por ejemplo `Fase TFM`) y faltan opciones en GitHub,
el script te pedira recrear ese campo manualmente en la UI para evitar inconsistencias.

Extra: si los issues ya existian (por ejecuciones previas), el script intenta dejar coherentes:
- labels `tipo/...` y `fase/...`
- milestone correspondiente a la fase

## 4) Vistas/tableros recomendados en GitHub Projects

El API del MVP crea datos y campos. Luego, en la UI del Project:

1. Vista `Kanban Estado`: Board agrupado por `Estado TFM`
2. Vista `Roadmap Fases`: Table filtrada/agrupada por `Fase TFM`
3. Vista `Trabajo por tipo`: Table agrupada por `Tipo TFM`

Con esto replicas el flujo Kanban de `docs/planificacion_kanban.md` en GitHub.

## 5) Ajustar tareas/fases sin tocar codigo

Edita solo:
- `scripts/planning/github_project_mvp.json`

Campos editables:
- `project_title`
- `estado_options`
- `tipo_options`
- `phases[].name`
- `phases[].milestone`
- `phases[].tasks[]`

Despues vuelve a ejecutar:

```powershell
python .\scripts\planning\bootstrap_github_project.py --apply
```
