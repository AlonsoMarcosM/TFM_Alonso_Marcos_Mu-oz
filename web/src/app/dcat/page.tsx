import { ArtifactViewer } from "@/components/ArtifactViewer";
import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function DcatPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">DCAT-AP-ES</h1>
        <p className="lead">Exporta el catálogo JSON-LD y valida contra las SHACL locales congeladas.</p>
      </header>
      <OperationGrid operations={operations.filter((operation) => ["export-dcat", "validate-dcat"].includes(operation.id))} />
      <ArtifactViewer initialPath="tmp_pytest/web_catalog.jsonld" />
    </div>
  );
}
