# Publicación gratuita de la consola web

## Propósito

La publicación de portfolio permite recorrer la **Plataforma de Gobierno del Dato** sin mantener Kubernetes, PostgreSQL ni OpenMetadata activos. Sirve artefactos congelados de una ejecución real y bloquea cualquier escritura o lanzamiento de procesos.

## Configuración

- URL pública: <https://tfm-plataforma-gobierno-dato.vercel.app>.
- Directorio de proyecto: `web/`.
- Proveedor: Vercel Hobby para uso académico no comercial.
- Variables de build y runtime: `TFM_DEMO=1` y `NEXT_PUBLIC_TFM_DEMO=1`.
- Dependencias y comandos: `pnpm install`, `pnpm test`, `pnpm build`.

La implementación detallada y el procedimiento de actualización de fixtures permanecen en `docs/app_web.md` y `web/demo/README.md`.

## Garantías

- `POST /api/jobs` devuelve resultados congelados y no ejecuta comandos.
- Las rutas de edición responden 403.
- No se leen `.env`, tokens ni rutas externas al directorio de fixtures.
- Las respuestas públicas ocultan rutas locales conservadas en evidencias históricas.

Estado: desplegado desde `main` y verificado públicamente.

Última verificación: 2026-06-22. Resultado: HTTP 200, modo de solo lectura activo, 18 artefactos, 14 ejecuciones congeladas, ejecución simulada con HTTP 201 y escrituras rechazadas con HTTP 403. La validación local pasó 45 tests Python, 15 tests web y el build de Next.js.
