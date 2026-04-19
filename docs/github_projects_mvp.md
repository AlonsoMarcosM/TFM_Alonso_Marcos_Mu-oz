# MVP GitHub Projects Para Planificación Del TFM

Objetivo: sustituir Microsoft Planner por un flujo reproducible en GitHub Projects v2, creado y actualizado por código.

Este MVP crea o actualiza de forma idempotente:

- Project v2 del TFM.
- Campos `Status`, `Fase TFM`, `Tipo TFM`, `fecha_inicio` y `fecha_fin`.
- Labels por tipo y fase.
- Milestones por fase.
- Issues base del roadmap extraídas de la configuración declarativa del repo.
- Alta de issues en el Project y asignación de campos.
- Enlace del Project al repositorio para que aparezca en `/<owner>/<repo>/projects`.
- Eliminación del campo legado `Estado TFM` para que no duplique el `Status` nativo de GitHub Projects.

El roadmap se toma del orden canónico definido en:

- `docs/planificacion_kanban.md`
- `01_Planificacion -> 02_Modelo_DCAT-AP-ES -> 03_OpenMetadata_Config -> 04_Pipeline_Ingesta -> 05_Validacion -> 06_Memoria`

## Archivos

- Script: `scripts/planning/bootstrap_github_project.py`
- Configuración declarativa: `scripts/planning/github_project_mvp.json`

## Seguridad Y Tokens

Codex no debe pedir tu contraseña de GitHub ni guardar tokens en archivos del repositorio. Hay dos formas válidas de operar:

- Token temporal de sesión: tú defines `GITHUB_TOKEN` o `GH_TOKEN` en la terminal actual y Codex puede usarlo mientras dure esa sesión.
- Token persistente de usuario: tú defines `GITHUB_TOKEN` como variable de entorno de Windows a nivel de usuario; así futuras sesiones de terminal y de agente pueden usarlo sin que el token esté en el repositorio.
- Archivo `.env` local: rellenas `.env` a partir de `.env.example` y lo cargas con `scripts/load_env.ps1`. Este archivo está ignorado por Git y no debe versionarse.

No uses `.env` versionados para tokens. La plantilla versionable es `.env.example`.

## Permisos Del Token

Para actualizar el tablero e issues se necesita un token con permisos de escritura sobre Projects e Issues.

Opción PAT classic:

- `repo`
- `project`
- `read:user`
- `read:org` solo si el owner fuera una organización

Opción fine-grained PAT:

- Account permissions: `Projects` con lectura/escritura.
- Repository permissions sobre el repo objetivo: `Issues` con lectura/escritura y `Metadata` de solo lectura.

## Configurar Token Temporal

Este modo no persiste al cerrar la terminal:

```powershell
$env:GITHUB_TOKEN="<TOKEN>"
$env:GITHUB_OWNER="AlonsoMarcosM"
$env:GITHUB_REPO="TFM_Alonso_Marcos_Mu-oz"
```

Comprobar que existe token sin imprimirlo:

```powershell
if ($env:GITHUB_TOKEN -or $env:GH_TOKEN) { "TOKEN_OK" } else { "NO_TOKEN" }
```

## Configurar Token En `.env` Local

Copia la plantilla y rellena el token:

```powershell
Copy-Item .env.example .env
notepad .env
```

Carga las variables en la terminal actual:

```powershell
. .\scripts\load_env.ps1
```

Comprobar sin mostrar el token:

```powershell
if ($env:GITHUB_TOKEN -or $env:GH_TOKEN) { "TOKEN_OK" } else { "NO_TOKEN" }
```

## Configurar Token Persistente En Windows

Este modo permite que Codex lo use en futuras sesiones sin pedirlo otra vez:

```powershell
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "<TOKEN>", "User")
[Environment]::SetEnvironmentVariable("GITHUB_OWNER", "AlonsoMarcosM", "User")
[Environment]::SetEnvironmentVariable("GITHUB_REPO", "TFM_Alonso_Marcos_Mu-oz", "User")
[Environment]::SetEnvironmentVariable("GITHUB_PROJECT_NUMBER", "6", "User")
```

Después cierra y abre una nueva terminal o una nueva sesión de Codex para que herede las variables.

Comprobar sin exponer el token:

```powershell
[bool][Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "User")
```

Eliminar el token si quieres revocar el acceso local:

```powershell
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", $null, "User")
```

## Dry-Run Local

Desde la raíz del repo:

```powershell
python .\scripts\planning\bootstrap_github_project.py --project-number 6
```

La salida esperada es un JSON con conteos, preview de labels, milestones, issues y campos del proyecto. No toca GitHub si no se pasa `--apply`.

## Actualizar El Project Real

El script no es solo un reflejo local: con `--apply` usa la API de GitHub para crear o actualizar labels, milestones, issues, items del Project y los campos `Status`, `Fase TFM`, `Tipo TFM`, `fecha_inicio` y `fecha_fin`.

Para actualizar el tablero real `https://github.com/users/AlonsoMarcosM/projects/6`, usa `--project-number 6`. Esto evita crear otro Project por error aunque cambie el título.

El script resuelve credenciales en este orden:

- `GITHUB_TOKEN`
- `GH_TOKEN`
- sesión activa de GitHub CLI mediante `gh auth token`

Además, si existe `.env` en la raíz, lo carga antes de resolver `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_PROJECT_NUMBER` y el token.

```powershell
python .\scripts\planning\bootstrap_github_project.py --apply --project-number 6
```

Si se crea un Project nuevo en otro entorno, puede omitirse `--project-number` y usar el título de `github_project_mvp.json`.

## Comportamiento Idempotente

Si ejecutas el script varias veces:

- No duplica labels.
- No duplica milestones.
- No duplica issues, porque compara por título con prefijo `[TFM]`.
- No duplica items en el Project.
- Vuelve a aplicar valores de campos para mantener coherencia.
- Sincroniza las fechas declaradas en `fecha_inicio` y `fecha_fin` para vistas de roadmap/Gantt.
- Borra el campo legado `Estado TFM` si existe, porque el estado canónico pasa a ser `Status`.
- Si los issues ya existían, intenta dejar coherentes labels `tipo/...`, labels `fase/...` y milestone.

Nota: si cambias las opciones de un campo single-select existente y faltan opciones en GitHub, el script falla de forma explícita. Es más seguro recrear manualmente ese campo en la UI que modificar opciones de forma opaca.

## Ajustar Tareas Sin Tocar Código

Edita solo:

- `scripts/planning/github_project_mvp.json`

Campos editables:

- `project_title`
- `status_options`
- `tipo_options`
- `phases[].name`
- `phases[].milestone`
- `phases[].tasks[]`
- `phases[].tasks[].fecha_inicio`
- `phases[].tasks[].fecha_fin`

Después vuelve a ejecutar:

```powershell
python .\scripts\planning\bootstrap_github_project.py --apply --project-number 6
```

## Acciones Destructivas

Borrar todos los Projects v2 del owner:

```powershell
$env:GITHUB_TOKEN="<TOKEN>"
python .\scripts\planning\bootstrap_github_project.py --delete-projects --confirm DELETE_ALL_PROJECTS --owner AlonsoMarcosM
```

Borrar milestones antiguas que no pertenecen al roadmap actual:

```powershell
$env:GITHUB_TOKEN="<TOKEN>"
python .\scripts\planning\bootstrap_github_project.py --delete-old-milestones --confirm DELETE_OLD_MILESTONES --owner AlonsoMarcosM --repo TFM_Alonso_Marcos_Mu-oz
```

## Vistas Recomendadas

El API del MVP crea datos y campos. Luego, en la UI del Project:

1. Vista `Kanban Estado`: board agrupado por `Status`.
2. Vista `Roadmap Fases`: tabla filtrada o agrupada por `Fase TFM`.
3. Vista `Gantt/Roadmap`: roadmap usando `fecha_inicio` y `fecha_fin`.
4. Vista `Trabajo por tipo`: tabla agrupada por `Tipo TFM`.

Con esto replicas el flujo Kanban de `docs/planificacion_kanban.md` en GitHub.
