import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

const resetOrder = [
  "Comprobar prerrequisitos.",
  "Backup estado OpenMetadata si se quiere conservar evidencia previa.",
  "Reset limpio y recrear la plataforma para partir de cluster y datos nuevos.",
  "Ingesta y Gobierno para revisar o ajustar la hoja funcional.",
  "Workflow y Validación para cerrar evidencias.",
];

export default function InfraestructuraPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Infraestructura y reset</h1>
        <p className="lead">
          Operaciones para preparar, reiniciar o recrear la plataforma sin memorizar comandos. Los botones ejecutan los
          mismos scripts versionados del repositorio.
        </p>
      </header>
      <section className="grid">
        <article className="card">
          <h2>Reset limpio</h2>
          <p className="muted">
            Usa <strong>Reset limpio y recrear la plataforma</strong> cuando quieras ejecutar el caso de uso de validación desde cero: elimina el
            cluster, aparta el snapshot para no restaurar datos anteriores y ejecuta el flujo completo.
          </p>
        </article>
        <article className="card">
          <h2>Orden recomendado</h2>
          <ol>
            {resetOrder.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </article>
        <article className="card">
          <h2>Port-forward</h2>
          <p className="muted">
            <code>port_forward_openmetadata.ps1</code> es un proceso persistente. No se lanza como job normal para
            evitar dejar un botón bloqueado; los jobs internos abren port-forward temporal cuando lo necesitan.
          </p>
        </article>
      </section>
      <OperationGrid operations={operations.filter((operation) => operation.group === "Infraestructura")} />
    </div>
  );
}
