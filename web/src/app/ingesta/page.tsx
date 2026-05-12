import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function IngestaPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Ingesta y preparación</h1>
        <p className="lead">
          Punto de entrada para una plataforma ya desplegada: conectar OpenMetadata con el PostgreSQL de referencia,
          lanzar la ingesta técnica y preparar los tags/custom properties que necesita el workflow de gobierno.
        </p>
      </header>
      <section className="grid">
        <article className="card">
          <h2>Qué aporta al catálogo</h2>
          <p className="muted">
            La ingesta convierte el servicio PostgreSQL en activos técnicos dentro de OpenMetadata: servicio, base de
            datos, esquemas, tablas y columnas. Es la base sobre la que después se gobiernan los datasets gold.
          </p>
        </article>
        <article className="card">
          <h2>Orden recomendado</h2>
          <ol>
            <li>Vaciar PostgreSQL de referencia en OpenMetadata, si quieres repetir el caso de uso desde el estado actual.</li>
            <li>Ingestar PostgreSQL de referencia.</li>
            <li>Preparar tags y custom properties.</li>
            <li>Revisar Gobierno.</li>
            <li>Ejecutar Workflow.</li>
          </ol>
        </article>
        <article className="card">
          <h2>Requisito previo</h2>
          <p className="muted">
            Esta pantalla asume que Kubernetes/OpenMetadata/PostgreSQL ya están levantados. Si no lo están,
            usa Infraestructura o Preparación antes de continuar.
          </p>
        </article>
      </section>
      <OperationGrid operations={operations.filter((operation) => operation.group === "Ingesta")} />
    </div>
  );
}
