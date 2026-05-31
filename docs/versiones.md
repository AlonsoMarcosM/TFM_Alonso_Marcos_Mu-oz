# Matriz de versiones del sistema

Todas las versiones del sistema deben estar **fijadas y documentadas** para garantizar
reproducibilidad. Esta es la referencia única; la memoria la recoge en el anexo de
infraestructura (sección «Matriz de versiones del sistema»).

| Componente | Versión | Dónde se fija |
| --- | --- | --- |
| OpenMetadata (app y charts) | `1.12.9` | `--version` en `scripts/infra/launch_infra.ps1` |
| Helm (CLI) | `3.14.4` | `.tools/helm-v3.14.4/` (descarga local del repo) |
| Kind | `0.31.0` | prerrequisito (`scripts/infra/check_prereqs.ps1`) |
| kubectl | `1.34.1` | prerrequisito |
| Docker Engine | `28.5.1` | prerrequisito |
| Python | `3.12` (mínimo `3.10`) | `tfm_ingestor/pyproject.toml` (`requires-python`) |
| Node.js | `22.11` | prerrequisito de `web/` |
| pnpm | `11.x` | gestor Node canónico del repositorio |
| Next.js | `16.2` | `web/package.json` |
| React | `19.2` | `web/package.json` |
| TypeScript | `6.0` | `web/package.json` |
| vitest | `4.1` | `web/package.json` |
| MySQL / OpenSearch | gestionados por `openmetadata-dependencies 1.12.9` | chart Helm |
| pyshacl | `>= 0.28` | extra `validation` en `pyproject.toml` |
| PyJWT | `>= 2.8` | extra `infra` en `pyproject.toml` |
| cryptography | `>= 42.0` | extra `infra` en `pyproject.toml` |
| fpdf2 | `>= 2.7` | extra `report` en `pyproject.toml` |
| PyYAML / requests | `>= 6.0` / `>= 2.31` | dependencias base en `pyproject.toml` |
| Bundle SHACL DCAT-AP-ES | `1.0.0`, commit `f2c8a88868b89239c9f54bffdf621cded2401b9f` (2026-04-13) | `tfm_ingestor/src/tfm_ingestor/resources/shacl/manifest.json` |
| Perfil DCAT-AP-ES | `1.0.0` | documentación oficial datos.gob.es |
| DCAT-AP base | `2.1.1` | documentación oficial SEMIC |
| DCAT-AP HVD | `2.2.0` | documentación oficial |

## Comprobar la versión viva de OpenMetadata

```powershell
Invoke-RestMethod http://localhost:8585/api/v1/system/version
```

## Comprobar versiones de herramientas locales

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\check_prereqs.ps1 -Strict
# Informe JSON en tmp_pytest/prereqs_report.json
```

## Notas

- El chart de OpenMetadata se instala con `--version 1.12.9`; sin fijarlo, Helm tomaría
  la última versión publicada y rompería la reproducibilidad.
- Los extras de Python (`infra`, `validation`, `report`) usan cotas mínimas (`>=`) para
  tolerar parches de seguridad; las versiones exactas instaladas quedan registradas en el
  entorno (`python -m pip freeze`).
- El bundle SHACL está congelado por commit, de modo que la validación no depende de la red.
