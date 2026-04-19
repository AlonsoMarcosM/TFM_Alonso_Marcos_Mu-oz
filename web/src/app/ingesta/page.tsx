import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function IngestaPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Ingesta y preparación</h1>
        <p className="lead">
          Punto de entrada para una PoC ya desplegada: conectar OpenMetadata con el PostgreSQL demo,
          lanzar la ingesta técnica y preparar los tags/custom properties que necesita el workflow de gobierno.
        </p>
      </header>
      <section className="grid">
        <article className="card">
          <h2>Orden recomendado</h2>
          <ol>
            <li>Ingestar PostgreSQL demo.</li>
            <li>Preparar tags y custom properties.</li>
            <li>Revisar Gobierno.</li>
            <li>Ejecutar Workflow.</li>
          </ol>
        </article>
        <article className="card">
          <h2>Requisito previo</h2>
          <p className="muted">
            Esta pantalla asume que Kubernetes/OpenMetadata/PostgreSQL ya están levantados. Si no lo están,
            usa los comandos de Preparación antes de continuar.
          </p>
        </article>
      </section>
      <OperationGrid operations={operations.filter((operation) => operation.group === "Ingesta")} />
    </div>
  );
}
