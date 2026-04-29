import { OperationGrid } from "@/components/OperationGrid";
import { listArtifacts } from "@/server/artifacts";
import { envStatus } from "@/server/env";
import { operations } from "@/server/operations";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const env = envStatus();
  const artifacts = await listArtifacts();
  const quick = operations.filter((operation) =>
    [
      "ingest-postgres",
      "bootstrap-governance",
      "refresh-governance-sheet",
      "validate-governance-sheet",
      "workflow-dry-run",
      "workflow-apply",
      "run-validation-suite",
    ].includes(operation.id),
  );

  return (
    <div className="stack">
      <header>
        <h1 className="page-title">PoC DCAT-AP-ES sobre OpenMetadata</h1>
        <p className="lead">Consola simple para ejecutar el flujo ya construido: gobierno gold, workflow, exportación, validación y evidencias.</p>
      </header>
      <section className="grid">
        <article className="card">
          <h2>Configuración</h2>
          <p>.env: {env.exists ? "detectado" : "no detectado"}</p>
          {env.required.map((item) => (
            <p key={item.name} className="muted">
              {item.name}: {item.present ? "presente" : "falta"}
            </p>
          ))}
        </article>
        <article className="card">
          <h2>Evidencias recientes</h2>
          {artifacts.filter((artifact) => artifact.exists).slice(0, 5).map((artifact) => (
            <p key={artifact.path} className="muted">{artifact.path}</p>
          ))}
        </article>
      </section>
      <section>
        <h2>Acciones principales</h2>
        <OperationGrid operations={quick} />
      </section>
    </div>
  );
}
