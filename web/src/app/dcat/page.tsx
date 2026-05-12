import { ArtifactViewer } from "@/components/ArtifactViewer";
import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function DcatPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">DCAT-AP-ES</h1>
        <p className="lead">
          Exporta el catálogo RDF serializado en JSON-LD y valida contra las SHACL locales congeladas de DCAT-AP-ES.
        </p>
      </header>
      <section className="panel">
        <h2>Uso de negocio</h2>
        <p className="muted">
          El JSON-LD generado representa el catálogo UCLM gobernado y queda preparado para interoperabilidad con
          portales compatibles como datos.gob.es o data.europa.eu. Esta pantalla no publica en portales externos.
        </p>
      </section>
      <OperationGrid operations={operations.filter((operation) => ["export-dcat", "validate-dcat"].includes(operation.id))} />
      <ArtifactViewer initialPath="tmp_pytest/web_catalog.jsonld" />
    </div>
  );
}
