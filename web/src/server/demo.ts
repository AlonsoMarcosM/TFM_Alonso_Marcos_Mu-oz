/**
 * Modo demo (solo lectura) de la consola web.
 *
 * Cuando `TFM_DEMO` está activo, la consola no ejecuta scripts ni habla con
 * OpenMetadata/Kubernetes: sirve artefactos congelados de una ejecución real
 * previa desde `web/demo/`. Pensado para desplegar la web en hosting estático
 * gratuito (Vercel) sin la infraestructura por debajo.
 */
export function isDemoMode(): boolean {
  const value = process.env.TFM_DEMO;
  return value === "1" || value === "true";
}
