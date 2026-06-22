# Publicación gratuita de la consola web

## Propósito

La publicación de portfolio permite recorrer la **Plataforma de Gobierno del Dato** sin mantener Kubernetes, PostgreSQL ni OpenMetadata activos. Sirve artefactos congelados de una ejecución real y bloquea cualquier escritura o lanzamiento de procesos.

## Configuración

- Directorio de proyecto: `web/`.
- Proveedor previsto: Vercel Hobby para uso académico no comercial.
- Variables de build y runtime: `TFM_DEMO=1` y `NEXT_PUBLIC_TFM_DEMO=1`.
- Dependencias y comandos: `pnpm install`, `pnpm test`, `pnpm build`.

La implementación detallada y el procedimiento de actualización de fixtures permanecen en `docs/app_web.md` y `web/demo/README.md`.

## Garantías

- `POST /api/jobs` devuelve resultados congelados y no ejecuta comandos.
- Las rutas de edición responden 403.
- No se leen `.env`, tokens ni rutas externas al directorio de fixtures.
- Los artefactos publicados no contienen rutas locales ni credenciales.

Estado: código publicado en `main`; despliegue de Vercel pendiente de autenticación OAuth.

Última verificación local: 2026-06-22, 45 tests Python, 13 tests web, build Next.js y smoke runtime correctos.
