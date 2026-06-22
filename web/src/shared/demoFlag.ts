/**
 * Indicador de modo demo para componentes cliente.
 *
 * `NEXT_PUBLIC_TFM_DEMO` se incrusta en el bundle en tiempo de build, por lo que
 * los componentes "use client" pueden leerlo para desactivar acciones de
 * escritura y mostrar el aviso de solo lectura. El equivalente de servidor es
 * `isDemoMode()` en `@/server/demo`.
 */
export const DEMO_MODE =
  process.env.NEXT_PUBLIC_TFM_DEMO === "1" || process.env.NEXT_PUBLIC_TFM_DEMO === "true";
